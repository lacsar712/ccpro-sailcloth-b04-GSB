from rest_framework.permissions import BasePermission

from accounts.models import User


class IsAdminRole(BasePermission):
    """仅管理员（role=admin 或超级用户）可执行写操作。"""

    message = "仅管理员可修改备注字数规则"

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (getattr(user, "role", None) == User.ROLE_ADMIN or user.is_superuser)
        )
