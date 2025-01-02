# core/utils.py

def is_pma_admin(user):
    """
    Check if the given user is a PMA admin.
    
    Args:
        user: The user object to check.
    
    Returns:
        bool: True if the user is a PMA admin, False otherwise.
    """
    return hasattr(user, 'userprofile') and user.userprofile.is_pma_admin()