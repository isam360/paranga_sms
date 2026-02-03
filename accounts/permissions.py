from rest_framework.permissions import BasePermission

class IsAcademicOfficer(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'academic_officer'

class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'teacher'
