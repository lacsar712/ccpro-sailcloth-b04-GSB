from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from core.models import ClothRoll, DipRun, Loft, NoteLengthPolicy
from core.rules import note_han_char_count, validate_dip_note


class NotePolicyApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            "root", password="x", role=User.ROLE_ADMIN
        )
        self.worker = User.objects.create_user(
            "gum1", password="x", role=User.ROLE_WORKER
        )
        self.loft = Loft.objects.create(name="北岸帆布间")
        self.roll = ClothRoll.objects.create(
            loft=self.loft, roll_code="R-01", status=ClothRoll.STATUS_RAW
        )

    def dip_payload(self, notes):
        return {
            "rollId": self.roll.id,
            "startedAt": timezone.now().isoformat(),
            "resinPct": "28.50",
            "cureHours": None,
            "notes": notes,
        }

    # ---- 策略端点权限与校验 ----

    def test_default_policy_exists_and_readable(self):
        for user in (self.admin, self.worker):
            self.client.force_authenticate(user)
            r = self.client.get("/api/note-policy/")
            self.assertEqual(r.status_code, status.HTTP_200_OK)
            self.assertEqual(r.data["minChars"], 1)
            self.assertEqual(r.data["maxChars"], 200)

    def test_admin_sets_bounds_worker_cannot(self):
        self.client.force_authenticate(self.admin)
        r = self.client.put(
            "/api/note-policy/", {"minChars": 3, "maxChars": 8}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.data)
        self.assertEqual(NoteLengthPolicy.objects.count(), 1)  # 始终单例
        policy = NoteLengthPolicy.load()
        self.assertEqual((policy.min_chars, policy.max_chars), (3, 8))

        self.client.force_authenticate(self.worker)
        r = self.client.put(
            "/api/note-policy/", {"minChars": 1, "maxChars": 2}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        # 未被改动
        policy.refresh_from_db()
        self.assertEqual((policy.min_chars, policy.max_chars), (3, 8))

    def test_bounds_must_be_valid(self):
        self.client.force_authenticate(self.admin)
        r = self.client.put(
            "/api/note-policy/", {"minChars": 0, "maxChars": 5}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        r = self.client.put(
            "/api/note-policy/", {"minChars": 9, "maxChars": 5}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    # ---- 浸渍备注闸门（面板 / 台账同一入口） ----

    def test_short_note_rejected_and_not_persisted(self):
        self.client.force_authenticate(self.admin)
        self.client.put(
            "/api/note-policy/", {"minChars": 3, "maxChars": 8}, format="json"
        )
        before = DipRun.objects.count()
        r = self.client.post("/api/dips/", self.dip_payload("太短"), format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("notes", r.data)
        self.assertEqual(DipRun.objects.count(), before)  # 整笔拒绝，未先插入
        self.assertFalse(DipRun.objects.filter(notes="太短").exists())

    def test_in_range_note_persists(self):
        self.client.force_authenticate(self.admin)
        self.client.put(
            "/api/note-policy/", {"minChars": 3, "maxChars": 8}, format="json"
        )
        self.client.force_authenticate(self.worker)
        r = self.client.post(
            "/api/dips/", self.dip_payload("三锅正常浸渍"), format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.data)
        self.assertTrue(DipRun.objects.filter(notes="三锅正常浸渍").exists())

    def test_too_long_note_rejected(self):
        self.client.force_authenticate(self.admin)
        self.client.put(
            "/api/note-policy/", {"minChars": 1, "maxChars": 3}, format="json"
        )
        r = self.client.post(
            "/api/dips/", self.dip_payload("一二三四五六"), format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DipRun.objects.count(), 0)

    def test_empty_note_is_exempt(self):
        self.client.force_authenticate(self.admin)
        self.client.put(
            "/api/note-policy/", {"minChars": 3, "maxChars": 8}, format="json"
        )
        for blank in ("", "   \t"):
            r = self.client.post("/api/dips/", self.dip_payload(blank), format="json")
            self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.data)

    def test_only_han_chars_count(self):
        self.assertEqual(note_han_char_count("AB12，。？ 短"), 1)
        policy = NoteLengthPolicy(min_chars=3, max_chars=6)
        ok, _ = validate_dip_note("AB12??短", policy)
        self.assertFalse(ok)
        ok, _ = validate_dip_note("一二三四", policy)
        self.assertTrue(ok)

    def test_two_writers_only_in_range_one_remains(self):
        """两名浸胶工交叉写同一卷：一条短于下限、一条落区间，只留合格那笔。"""
        self.client.force_authenticate(self.admin)
        self.client.put(
            "/api/note-policy/", {"minChars": 3, "maxChars": 10}, format="json"
        )

        self.client.force_authenticate(self.worker)
        other = User.objects.create_user("gum2", password="x", role=User.ROLE_WORKER)

        r_short = self.client.post("/api/dips/", self.dip_payload("短"), format="json")
        self.assertEqual(r_short.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(other)
        r_ok = self.client.post(
            "/api/dips/", self.dip_payload("四锅浸渍合格"), format="json"
        )
        self.assertEqual(r_ok.status_code, status.HTTP_201_CREATED, r_ok.data)

        notes = list(DipRun.objects.values_list("notes", flat=True))
        self.assertEqual(notes, ["四锅浸渍合格"])

    # ---- 其他动作不看字数 ----

    def test_roll_status_and_cure_ignore_note_length(self):
        self.client.force_authenticate(self.admin)
        self.client.put(
            "/api/note-policy/", {"minChars": 3, "maxChars": 8}, format="json"
        )
        # 改卷态、标已固化与浸渍备注字数无关；先补一条带固化时长的浸渍（空备注豁免）
        self.client.post("/api/dips/", self.dip_payload(""), format="json")
        dip = DipRun.objects.get()
        dip.cure_hours = "14"
        dip.save()
        r = self.client.patch(
            f"/api/rolls/{self.roll.id}/",
            {"status": "cured"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.data)
        self.roll.refresh_from_db()
        self.assertEqual(self.roll.status, ClothRoll.STATUS_CURED)
