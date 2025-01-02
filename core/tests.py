import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from .models import Announcement, BudgetItem, File, OrganizationJoinRequest, OrganizationMembership, Project, Organization, ProjectMembership, UserProfile, CalendarEvent, TodoItem
from .forms import ProjectForm, UserProfileForm, OrganizationForm, TodoForm, BudgetItemForm, EventForm


class ModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.organization = Organization.objects.create(name='Test Org', owner=self.user)
        self.project = Project.objects.create(
            title='Test Project',
            owner=self.user,
            organization=self.organization,
            description='Test description',
            priority='medium'
        )

    def test_project_creation(self):
        self.assertTrue(isinstance(self.project, Project))
        self.assertEqual(self.project.__str__(), self.project.title)
        self.assertEqual(self.project.status, 'active')
        self.assertEqual(self.project.priority, 'medium')
    
    def test_project_deletion(self):
        self.project.delete()
        self.assertEqual(self.project.status, 'deleted')

    def test_organization_creation(self):
        self.assertTrue(isinstance(self.organization, Organization))
        self.assertEqual(self.organization.__str__(), self.organization.name)
        self.assertTrue(self.organization.slug)
    
    def test_organization_unique_slug(self):
        org2 = Organization.objects.create(
            name='Test Org',
            owner=self.user
        )
        self.assertNotEqual(self.organization.slug, org2.slug)

    def test_user_profile_creation(self):
        self.assertTrue(hasattr(self.user, 'userprofile'))
        self.assertTrue(isinstance(self.user.userprofile, UserProfile))
        self.assertEqual(self.user.userprofile.user_type, 'common')

    def test_organization_membership(self):
        membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role='ADMIN'
        )
        self.assertEqual(membership.role, 'ADMIN')
        self.assertTrue(isinstance(membership, OrganizationMembership))
    
    def test_project_membership(self):
        membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.user,
            role='ADMIN',
            status='APPROVED'
        )
        self.assertEqual(membership.role, 'ADMIN')
        self.assertEqual(membership.status, 'APPROVED')

    def test_calendar_event_creation(self):
        event = CalendarEvent.objects.create(
            title='Test Event',
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
            user=self.user,
            project=self.project,
            location='Test Location'
        )
        self.assertTrue(isinstance(event, CalendarEvent))
        self.assertEqual(event.__str__(), event.title)
    
    def test_calendar_event_ordering(self):
        # Test ordering by start_time
        event1 = CalendarEvent.objects.create(
            title='Event 1',
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
            user=self.user,
            project=self.project
        )
        event2 = CalendarEvent.objects.create(
            title='Event 2',
            start_time=timezone.now() + timezone.timedelta(hours=2),
            end_time=timezone.now() + timezone.timedelta(hours=3),
            user=self.user,
            project=self.project
        )
        events = CalendarEvent.objects.all()
        self.assertEqual(events[0], event1)
        self.assertEqual(events[1], event2)

    def test_todo_item_creation(self):
        todo = TodoItem.objects.create(
            title='Test Todo',
            user=self.user,
            project=self.project,
            priority='high',
            description='Test todo description'
        )
        self.assertTrue(isinstance(todo, TodoItem))
        self.assertEqual(todo.__str__(), todo.title)
        self.assertEqual(todo.priority, 'high')

    def test_budget_item_creation(self):
        budget_item = BudgetItem.objects.create(
            project=self.project,
            description='Test Budget Item',
            amount=100.50,
            is_expense=True,
            date=timezone.now().date()
        )
        self.assertTrue(isinstance(budget_item, BudgetItem))
        self.assertEqual(budget_item.amount, 100.50)
    
# #     def test_file_upload(self):
#         test_file = SimpleUploadedFile(
#             "test.txt",
#             b"test content",
#             content_type="text/plain"
#         )
#         file = File.objects.create(
#             project=self.project,
#             uploaded_by=self.user,
#             file=test_file,
#             name='Test File',
#             description='Test file description'
#         )
#         self.assertTrue(isinstance(file, File))
#         self.assertEqual(file.name, 'Test File')
# 
    def test_announcement_creation(self):
        announcement = Announcement.objects.create(
            project=self.project,
            user=self.user,
            content='Test announcement'
        )
        self.assertTrue(isinstance(announcement, Announcement))
        self.assertTrue(announcement.is_visible)
    
    # def test_announcement_ordering(self):
    #     # Test ordering by created_at (latest first)
    #     announcement1 = Announcement.objects.create(
    #         project=self.project,
    #         user=self.user,
    #         content='Announcement 1'
    #     )
    #     announcement2 = Announcement.objects.create(
    #         project=self.project,
    #         user=self.user,
    #         content='Announcement 2'
    #     )
    #     announcements = Announcement.objects.all()
    #     self.assertEqual(announcements[0], announcement2)
    #     self.assertEqual(announcements[1], announcement1)

class FormTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.organization = Organization.objects.create(name='Test Org', owner=self.user)

    def test_project_form_valid(self):
        form_data = {
            'title': 'Test Project',
            'description': 'This is a test project',
            'status': 'active',
            'priority': 'medium',
            'organization': self.organization.id
        }
        form = ProjectForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_project_form_invalid(self):
        form_data = {
            'title': '',
            'description': 'This is a test project',
            'status': 'active'
        }
        form = ProjectForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_user_profile_form_valid(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'interests': 'Testing'
        }
        form = UserProfileForm(data=form_data, instance=self.user.userprofile)
        self.assertTrue(form.is_valid())

    def test_organization_form_valid(self):
        form_data = {
            'name': 'Test Organization',
            'description': 'This is a test organization',
            'category': 'academic',
            'size': 'small'
        }
        form = OrganizationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_organization_form_invalid_name(self):
        form_data = {
            'name': '',  # Invalid name (empty)
            'description': 'Description for invalid form',
            'category': 'academic',
            'size': 'small'
        }
        form = OrganizationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

class ExtendedModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.organization = Organization.objects.create(name='Test Org', owner=self.user)
        self.project = Project.objects.create(
            title='Test Project',
            owner=self.user,
            organization=self.organization,
            description='Extended model test description',
            priority='medium'
        )
    
# #     def test_file_search_fields_property(self):
#         test_file = SimpleUploadedFile("test.txt", b"test content", content_type="text/plain")
#         file = File.objects.create(
#             project=self.project,
#             uploaded_by=self.user,
#             file=test_file,
#             name='File with keywords',
#             description='Test file description',
#             keywords='keyword1, keyword2'
#         )
#         self.assertEqual(file.search_fields, ['File with keywords', 'Test file description', 'keyword1, keyword2'])
# 
    def test_organization_membership_unique_constraint(self):
        # Ensure uniqueness constraint on project and user combination in ProjectMembership
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='MEMBER')
        with self.assertRaises(Exception):
            OrganizationMembership.objects.create(organization=self.organization, user=self.user, role='MEMBER')
    
class ExtendedFormTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.organization = Organization.objects.create(name='Test Org', owner=self.user)

    def test_todo_form_valid(self):
        form_data = {
            'title': 'Todo Test Title',
            'description': 'Testing the todo form.',
            'due_date': timezone.now().date(),
            'priority': 'high'
        }
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_budget_item_form_valid(self):
        form_data = {
            'description': 'Test Budget Item',
            'amount': 50.25,
            'is_expense': True,
            'date': timezone.now().date()
        }
        form = BudgetItemForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_event_form_date_validation(self):
        # Testing end time before start time for EventForm
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = timezone.now()
        form_data = {
            'title': 'Event Test',
            'description': 'Event form test',
            'start_time': start_time,
            'end_time': end_time,
            'location': 'Test Location'
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('end_time', form.errors)
    
class ExtendedViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.organization = Organization.objects.create(name='Test Org', owner=self.user)
        self.project = Project.objects.create(
            title='Test Project',
            owner=self.user,
            organization=self.organization,
            description='Test project description',
            priority='medium',
            slug='test-project'  # Adding slug for URL usage
        )

# #     def test_project_create_view_redirect_for_unauthenticated_user(self):
#         self.client.logout()
#         response = self.client.get(reverse('create_project'))  # Updated to correct route name
#         self.assertEqual(response.status_code, 302)  # Should redirect to login
# 
# #     def test_announcement_create_view(self):
#         form_data = {
#             'content': 'New Announcement Content'
#         }
#         response = self.client.post(reverse('post_announcement', args=[self.project.slug]), data=form_data)  # Updated to correct route name
#         self.assertEqual(response.status_code, 302)  # Should redirect after successful announcement creation
#         self.assertTrue(Announcement.objects.filter(content='New Announcement Content').exists())
# 
# class AdditionalModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.organization = Organization.objects.create(name='Test Org', owner=self.user)
        self.project = Project.objects.create(
            title='Test Project',
            owner=self.user,
            organization=self.organization,
            description='Extended model test description',
            priority='medium',
            slug='test-project'
        )

    def test_default_project_status(self):
        # Ensuring that the default status of a project is 'active'
        self.assertEqual(self.project.status, 'active')

    def test_todo_priority_default(self):
        todo = TodoItem.objects.create(title='Low Priority Todo', user=self.user, project=self.project)
        # Verify default priority if none is set
        self.assertEqual(todo.priority, 'medium')  # Assuming medium is the default

    def test_calendar_event_duration(self):
        start_time = timezone.now()
        end_time = start_time + timezone.timedelta(hours=2)
        event = CalendarEvent.objects.create(
            title='Long Event', start_time=start_time, end_time=end_time, user=self.user, project=self.project
        )
        # Check that the event duration is calculated correctly
        self.assertEqual((event.end_time - event.start_time).seconds, 7200)

class ExtraFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.organization = Organization.objects.create(name='Test Org', owner=self.user)

    def test_project_form_title_max_length(self):
        form_data = {
            'title': 'A' * 201,  # Exceeding max length assuming title max length is 200
            'description': 'This is a test project.',
            'status': 'active',
            'priority': 'medium',
            'organization': self.organization.id
        }
        form = ProjectForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_todo_form_missing_due_date(self):
        form_data = {
            'title': 'Incomplete Todo',
            'priority': 'low',
        }
        form = TodoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('due_date', form.errors)  # Assuming due date is required

class AdditionalViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.organization = Organization.objects.create(name='Test Org', owner=self.user)
        self.project = Project.objects.create(
            title='Test Project',
            owner=self.user,
            organization=self.organization,
            description='Test project description',
            priority='medium',
            slug='test-project'
        )


# #     def test_unauthenticated_user_access_to_project_detail(self):
#         self.client.logout()
#         response = self.client.get(reverse('project_detail', args=[self.project.slug]))
#         self.assertEqual(response.status_code, 302)  # Should redirect to login page
# 
# #     def test_calendar_event_creation_no_location(self):
#         start_time = timezone.now()
#         end_time = start_time + timezone.timedelta(hours=1)
# 
#         form_data = {
#             'title': 'No Location Event',
#             'description': 'Testing without location',
#             'start': start_time.strftime('%Y-%m-%dT%H:%M'),
#             'end': end_time.strftime('%Y-%m-%dT%H:%M'),
#             'project_id': self.project.id
#         }
#         print(f"Form Data: {form_data}")  # Log form data to verify
# 
#         response = self.client.post(reverse('create_calendar_event'), 
#                               data=json.dumps(form_data),
#                               content_type='application/json') 
# 
# class ProjectDetailTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.user2 = User.objects.create_user(username='memberuser', password='12345')
        self.client.login(username='testuser', password='12345')
        
        self.project = Project.objects.create(
            title='Test Project',
            owner=self.user,
            description='A sample project',
            status='active',
            slug='test-project'
        )
        self.project.members.add(self.user2)

# #     def test_project_info_display(self):
#         response = self.client.get(reverse('project_detail', args=[self.project.slug]))
#         self.assertContains(response, 'Test Project')
#         self.assertContains(response, 'A sample project')
#         self.assertContains(response, 'active')
#         self.assertContains(response, self.user.username)
# 
# #     def test_buttons_for_project_owner(self):
#         response = self.client.get(reverse('project_detail', args=[self.project.slug]))
#         self.assertContains(response, 'Edit Project')
#         self.assertContains(response, 'Manage Members')
#         self.assertContains(response, 'Delete Project')
# 
# #     def test_buttons_for_project_member(self):
#         self.client.logout()
#         self.client.login(username='memberuser', password='12345')
#         response = self.client.get(reverse('project_detail', args=[self.project.slug]))
#         self.assertContains(response, 'Upload File')
#         self.assertContains(response, 'Add Todo')
#         self.assertContains(response, 'Add Event')
#         self.assertContains(response, 'Post Announcement')
#         
# #     def test_no_admin_buttons_for_non_owner(self):
#         self.client.logout()
#         self.client.login(username='memberuser', password='12345')
#         response = self.client.get(reverse('project_detail', args=[self.project.slug]))
#         self.assertNotContains(response, 'Edit Project')
#         self.assertNotContains(response, 'Manage Members')
#         self.assertNotContains(response, 'Delete Project')
#     
# #     def test_file_list_display(self):
#         file = File.objects.create(
#             project=self.project,
#             uploaded_by=self.user,
#             name='Sample File'
#         )
#         response = self.client.get(reverse('project_detail', args=[self.project.slug]))
#         self.assertContains(response, 'Sample File')
#         self.assertContains(response, 'Download')
#         
# #     def test_announcement_list_display(self):
#         announcement = Announcement.objects.create(
#             project=self.project,
#             user=self.user,
#             content='Project announcement'
#         )
#         response = self.client.get(reverse('project_detail', args=[self.project.slug]))
#         self.assertContains(response, 'Project announcement')
#         
# #     def test_todo_list_display(self):
#         todo = TodoItem.objects.create(
#             title='Sample Todo',
#             project=self.project,
#             user=self.user,
#             priority='high'
#         )
#         response = self.client.get(reverse('project_detail', args=[self.project.slug]))
#         self.assertContains(response, 'Sample Todo')
#         
# #     def test_event_list_display(self):
#         start_time = timezone.now()
#         end_time = start_time + timezone.timedelta(hours=1)
#         event = CalendarEvent.objects.create(
#             title='Project Event',
#             start_time=start_time,
#             end_time=end_time,
#             user=self.user,
#             project=self.project
#         )
#         response = self.client.get(reverse('project_detail', args=[self.project.slug]))
#         self.assertContains(response, 'No upcoming events.')
#         
# #     def test_budget_summary_display(self):
#         # Create an income item
#         BudgetItem.objects.create(
#             project=self.project,
#             description='Income Item',
#             amount=1000.00,
#             is_expense=False,
#             date=timezone.now().date()
#         )
#         # Create the expense item
#         BudgetItem.objects.create(
#             project=self.project,
#             description='Expense Item',
#             amount=500.00,
#             is_expense=True,
#             date=timezone.now().date()
#         )
# 
#         response = self.client.get(reverse('project_detail', args=[self.project.slug]))
#         self.assertContains(response, 'Total Income')
#         self.assertContains(response, 'Total Expenses')
#         self.assertContains(response, 'Balance')
#         self.assertContains(response, '+$1000.00')
#         self.assertContains(response, '-$500.00')
# 
# class UserDashboardTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345', email='testuser@example.com')
        self.client.login(username='testuser', password='12345')

# #     def test_dashboard_greeting_and_email_display(self):
#         response = self.client.get(reverse('dashboard'))
#         self.assertContains(response, 'Welcome, testuser!')
#         self.assertContains(response, 'testuser@example.com')
# 
# #     def test_search_bar_rendered(self):
#         response = self.client.get(reverse('dashboard'))
#         self.assertContains(response, 'Search for organizations, projects, or users...')
#         self.assertContains(response, '<button type="submit" class="btn btn-primary">Search</button>', html=True)
# 
# #     def test_calendar_controls_for_authenticated_user(self):
#         response = self.client.get(reverse('dashboard'))
#         self.assertContains(response, 'Add Event')
# 
# #     def test_todo_list_controls_rendered(self):
#         response = self.client.get(reverse('dashboard'))
#         self.assertContains(response, 'New task')
#         self.assertContains(response, 'Add')
#         self.assertContains(response, 'Clear Completed')
# 
# #     def test_no_projects_message_displayed(self):
#         response = self.client.get(reverse('dashboard'))
#         self.assertContains(response, "You don't have any projects yet.")
#         self.assertContains(response, "You're not a member of any projects yet.")
# 
# #     def test_no_organizations_message_displayed(self):
#         response = self.client.get(reverse('dashboard'))
#         self.assertContains(response, "You're not a member of any organizations yet.")
# 
# #     def test_user_owned_projects_displayed(self):
#         # Create a project owned by the user
#         project = Project.objects.create(title='User Project', owner=self.user, slug='user-project')
#         response = self.client.get(reverse('dashboard'))
#         self.assertContains(response, 'User Project')
# 
# #     def test_user_member_projects_displayed(self):
#         # Create a project where the user is a member
#         owner = User.objects.create_user(username='projectowner', password='12345')
#         project = Project.objects.create(title='Member Project', owner=owner, slug='member-project')
#         project.members.add(self.user)
#         response = self.client.get(reverse('dashboard'))
#         self.assertContains(response, 'Member Project')
# 
# #     def test_user_owned_organizations_displayed(self):
#         # Create an organization owned by the user
#         organization = Organization.objects.create(name='User Organization', owner=self.user)
#         response = self.client.get(reverse('dashboard'))
#         self.assertContains(response, 'User Organization')
# 
# #     def test_user_member_organizations_displayed(self):
#         # Create an organization where the user is a member
#         owner = User.objects.create_user(username='orgowner', password='12345')
#         organization = Organization.objects.create(name='Member Organization', owner=owner)
#         organization.members.add(self.user)
#         response = self.client.get(reverse('dashboard'))
#         self.assertContains(response, 'Member Organization')
# 
# class PostAnnouncementTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.project = Project.objects.create(title='Test Project', owner=self.user, slug='test-project')

# #     def test_post_announcement_submission(self):
#         response = self.client.post(reverse('post_announcement', args=[self.project.slug]), {
#             'content': 'New announcement content.'
#         })
#         self.assertEqual(response.status_code, 302)  # Expect a redirect on successful post
#         self.assertTrue(Announcement.objects.filter(content='New announcement content.').exists())
# 
# #     def test_invalid_form_submission_shows_errors(self):
#         response = self.client.post(reverse('post_announcement', args=[self.project.slug]), {})
#         self.assertContains(response, 'There were some errors with your submission:')
# 
# class CreateTodoTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.project = Project.objects.create(title='Test Project', owner=self.user, slug='test-project')
    '''
    def test_create_todo_submission(self):
        response = self.client.post(reverse('create_todo', args=[self.project.slug]), {
            'title': 'New Todo Task',
            'description': 'Task description here',
            'priority': 'high'
        })
        self.assertEqual(response.status_code, 302)  # Expect redirect after creation
        self.assertTrue(TodoItem.objects.filter(title='New Todo Task').exists())
'''
# #     def test_invalid_todo_form_submission(self):
#         response = self.client.post(reverse('create_todo', args=[self.project.slug]), {})
#         self.assertContains(response, 'This field is required')
# 
# class CreateTodoTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.project = Project.objects.create(title='Test Project', owner=self.user, slug='test-project')

# #     def test_invalid_todo_form_submission(self):
#         response = self.client.post(reverse('create_todo', args=[self.project.slug]), {})
#         self.assertContains(response, 'This field is required')
# 
# class ProjectFeedTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        # Create sample projects
        self.project1 = Project.objects.create(title='Active Project', status='active', owner=self.user)
        self.project2 = Project.objects.create(title='Completed Project', status='completed', owner=self.user)

# #     def test_project_feed_rendered(self):
#         response = self.client.get(reverse('project_feed'))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, 'Project Feed')
#         self.assertContains(response, 'Discover and collaborate on exciting projects in our community')
#         self.assertContains(response, 'Search projects...')
# 
# #     def test_projet_filter_buttons_displayed(self):
#         response = self.client.get(reverse('project_feed'))
#         self.assertContains(response, 'All')
#         self.assertContains(response, 'Active')
#         self.assertContains(response, 'Completed')
# 
# #     def test_project_sorting_options_displayed(self):
#         response = self.client.get(reverse('project_feed'))
#         self.assertContains(response, 'Newest First')
#         self.assertContains(response, 'Oldest First')
#         self.assertContains(response, 'Name (A-Z)')
#         self.assertContains(response, 'Name (Z-A)')
# 
# #     def test_authenticated_user_create_project_button(self):
#         response = self.client.get(reverse('project_feed'))
#         self.assertContains(response, 'Create Project')
# 
# #     def test_projects_displayed(self):
#         response = self.client.get(reverse('project_feed'))
#         self.assertContains(response, 'Active Project')
#         self.assertContains(response, 'Completed Project')
# 
# #     def test_no_projects_message(self):
#         # Delete all projects to test the "No Projects Found" message
#         Project.objects.all().delete()
#         response = self.client.get(reverse('project_feed'))
#         self.assertContains(response, 'No Projects Found')
#         self.assertContains(response, 'There are no projects available at the moment.')
# 
# 
