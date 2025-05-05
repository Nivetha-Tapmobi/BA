# permissions.py
def get_permissions(session, page_name=None):


    # Extract raw permissions from session, default to 0 if not found
    can_create = session.get('IOMS_can_create_Asset_Tracking_Industrial', 0)
    can_read = session.get('IOMS_can_read_Asset_Tracking_Industrial', 0)
    can_update = session.get('IOMS_can_update_Asset_Tracking_Industrial', 0)
    can_delete = session.get('IOMS_can_delete_Asset_Tracking_Industrial', 0)

   

    # Explicitly define role and dashboard route based on your conditions
    if can_create == 1 and can_read == 1 and can_update == 1 and can_delete == 1:
        role = 'admin'
        dashboard_route = 'it_dashboard'

    elif can_create == 1 and can_read == 1 and can_update == 1 and can_delete == 0:
        role = 'manager'
        dashboard_route = 'it_dashboard'
        print('manager role')
    elif can_read == 1 and can_create == 0 and can_update == 0 and can_delete == 0:
        role = 'employee'
        dashboard_route = 'view_assets'
        print('employeee role')
    else:
        role = None
        dashboard_route = None

    # If no page_name is provided or role is None, return only role and dashboard_route
    if page_name is None or role is None:
        return {
            'role': role,
            'dashboard_route': dashboard_route
        }

    # Define page-specific permissions
    page_permissions = {
        'view_assets': {
            'admin': [
                'add_asset', 'download_excel', 'view_details', 'edit', 
                'add_user', 'raise_ticket', 'ex_warranty', 'insurance', 'delete','view_raised_tickets'
            ],
            'manager': [
                'add_asset', 'download_excel', 'view_details', 'edit', 
                'add_user', 'raise_ticket', 'ex_warranty', 'insurance','view_raised_tickets'
            ],
            'employee': [
                'raise_ticket', 'download_excel'
            ]
        },
        'it_dashboard': {
            'admin': [
                'view', 'create_service', 'ignore', 'replacement', 'home_page', 
                'view_it_assets', 'view_service_details', 'raise_ticket', 'logout',
                'add_asset', 'view_raised_tickets', 'view_assets', 'view_service', 
                'view_insurance', 'view_extended_warranty', 'check_asset_status', 
                'all_assets', 'upcoming_alerts'
            ],
            'manager': [
                'view', 'create_service', 'ignore', 'replacement', 'home_page', 
                'view_it_assets', 'view_service_details', 'raise_ticket', 'logout',
                 'add_asset', 'view_raised_tickets', 'view_assets', 'view_service', 
                'view_insurance', 'view_extended_warranty', 'check_asset_status', 
                'all_assets', 'upcoming_alerts'
            ],
            'employee': [         
            ]
        },
        'header': {
            'admin': [
                'add_asset', 'view_raised_tickets', 'view_assets', 'view_service', 
                'view_insurance', 'view_extended_warranty', 'check_asset_status', 
                'all_assets', 'upcoming_alerts','logout','request_product','request_wfh_asset','it_dashboard'
            ],
            'manager': [
                'add_asset', 'view_raised_tickets', 'view_assets', 'view_service', 
                'view_insurance', 'view_extended_warranty', 'check_asset_status', 
                'all_assets', 'upcoming_alerts','logout','request_product','request_wfh_asset','it_dashboard'
            ],
            'employee': [
                'view_assets','logout','request_product','request_wfh_asset'
            ]
        },
        'view_extended_warranty': {  # Added permissions for this page
            'admin': ['view', 'edit', 'delete'],
            'manager': ['view', 'edit'],
            'employee': []  # No actions for employee
        },

        'view_insurance': {  # Added permissions for this page
            'admin': ['view', 'edit', 'delete'],
            'manager': ['view', 'edit'],
            'employee': []  # No actions for employee
        },

         'view_service': {  # Added permissions for this page
            'admin': ['view', 'edit', 'delete', ],
            'manager': ['view', 'edit'],
            'employee': []  # No actions for employee
        },

        'view_tickets': {  # Added permissions for this page
            'admin': ['view', 'edit', 'delete', 'create_service', 'ignore_ticket', 'replacement',
                      'add_asset', 'view_raised_tickets', 'view_assets', 'view_service', 
                'view_insurance', 'view_extended_warranty', 'check_asset_status', 
                'all_assets', 'upcoming_alerts','logout','reraise_ticket'],

            'manager': ['view', 'edit','create_service', 'ignore_ticket', 'replacement',
                        'add_asset', 'view_raised_tickets', 'view_assets', 'view_service', 
                'view_insurance', 'view_extended_warranty', 'check_asset_status', 
                'all_assets', 'upcoming_alerts','logout','reraise_ticket'],

            'employee': ['view_raised_tickets', 'logout', 'view_assets','reraise_ticket']  # No actions for employee
        },

        'view_users': {  # Added permissions for this page
            'admin': ['view', 'edit', 'delete',
                      'add_asset', 'view_raised_tickets', 'view_assets', 'view_service', 
                'view_insurance', 'view_extended_warranty', 'check_asset_status', 
                'all_assets', 'upcoming_alerts','logout'],
            'manager': ['view', 'edit',
                        'add_asset', 'view_raised_tickets', 'view_assets', 'view_service', 
                'view_insurance', 'view_extended_warranty', 'check_asset_status', 
                'all_assets', 'upcoming_alerts','logout'],
            'employee': ['view_raised_tickets', 'logout', 'view_assets']  # No actions for employee
        },

        'view_requested_products': {  # Added permissions for this page
            'admin': ['view', 'edit', 'delete', 'create_service', 'ignore_ticket', 'replacement',
                      'add_asset', 'view_raised_tickets', 'view_assets', 'view_service', 
                'view_insurance', 'view_extended_warranty', 'check_asset_status', 
                'all_assets', 'upcoming_alerts','logout','reraise_ticket'],

            'manager': ['view', 'edit','create_service', 'ignore_ticket', 'replacement',
                        'add_asset', 'view_raised_tickets', 'view_assets', 'view_service', 
                'view_insurance', 'view_extended_warranty', 'check_asset_status', 
                'all_assets', 'upcoming_alerts','logout','reraise_ticket'],

            'employee': ['view_raised_tickets', 'logout', 'view_assets','reraise_ticket']  # No actions for employee
        },

    }

    # Get the permissions for the requested page
    role_actions = page_permissions.get(page_name, {}).get(role, [])

    # Convert list to dictionary for template compatibility
    actions_dict = {action: True for action in role_actions}

    return {
        'role': role,
        'dashboard_route': dashboard_route,
        'permissions': actions_dict
    }