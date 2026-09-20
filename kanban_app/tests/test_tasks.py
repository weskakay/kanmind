from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import User
from kanban_app.models import Board, Task

PASSWORD = 'kanmind-4711!'


class TaskTestCase(APITestCase):
    """Shared board with an owner, a member and an outsider."""

    def setUp(self):
        self.owner = User.objects.create_user('a@example.com', 'A', PASSWORD)
        self.member = User.objects.create_user('b@example.com', 'B', PASSWORD)
        self.other = User.objects.create_user('c@example.com', 'C', PASSWORD)
        self.board = Board.objects.create(title='Sprint', owner=self.owner)
        self.board.members.set([self.owner, self.member])
        self.task = Task.objects.create(
            board=self.board,
            title='Write tests',
            created_by=self.owner,
            assignee=self.member,
            reviewer=self.owner,
        )


class TaskCreateTests(TaskTestCase):
    """Covers POST /api/tasks/."""

    def setUp(self):
        super().setUp()
        self.url = reverse('task-create')
        self.payload = {
            'board': self.board.id,
            'title': 'New task',
            'description': 'Something to do',
            'status': 'to-do',
            'priority': 'high',
            'assignee_id': self.member.id,
            'reviewer_id': self.owner.id,
            'due_date': '2026-10-01',
        }

    def test_member_can_create_a_task(self):
        self.client.force_authenticate(self.member)
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['assignee']['id'], self.member.id)
        self.assertEqual(response.data['reviewer']['id'], self.owner.id)
        self.assertEqual(response.data['comments_count'], 0)

    def test_creator_is_stored(self):
        self.client.force_authenticate(self.member)
        response = self.client.post(self.url, self.payload)
        task = Task.objects.get(pk=response.data['id'])
        self.assertEqual(task.created_by, self.member)

    def test_outsider_gets_403(self):
        self.client.force_authenticate(self.other)
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assignee_outside_the_board_returns_400(self):
        self.client.force_authenticate(self.owner)
        self.payload['assignee_id'] = self.other.id
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reviewer_outside_the_board_returns_400(self):
        self.client.force_authenticate(self.owner)
        self.payload['reviewer_id'] = self.other.id
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_board_returns_400(self):
        self.client.force_authenticate(self.owner)
        self.payload['board'] = 9999
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_title_returns_400(self):
        self.client.force_authenticate(self.owner)
        del self.payload['title']
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_status_returns_400(self):
        self.client.force_authenticate(self.owner)
        self.payload['status'] = 'flying'
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_requires_authentication(self):
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskDetailTests(TaskTestCase):
    """Covers PATCH and DELETE on /api/tasks/{id}/."""

    def setUp(self):
        super().setUp()
        self.url = reverse('task-detail', args=[self.task.id])

    def test_member_can_patch_the_task(self):
        self.client.force_authenticate(self.member)
        response = self.client.patch(self.url, {'status': 'done'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'done')

    def test_patch_answer_has_no_board_and_no_comment_count(self):
        self.client.force_authenticate(self.member)
        response = self.client.patch(self.url, {'status': 'review'})
        self.assertNotIn('board', response.data)
        self.assertNotIn('comments_count', response.data)

    def test_patch_cannot_move_the_task_to_another_board(self):
        other_board = Board.objects.create(title='Other', owner=self.owner)
        self.client.force_authenticate(self.owner)
        self.client.patch(self.url, {'board': other_board.id})
        self.task.refresh_from_db()
        self.assertEqual(self.task.board, self.board)

    def test_patch_with_outside_assignee_returns_400(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            self.url, {'assignee_id': self.other.id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_outsider_cannot_patch(self):
        self.client.force_authenticate(self.other)
        response = self.client.patch(self.url, {'status': 'done'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_creator_can_delete(self):
        self.client.force_authenticate(self.owner)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.count(), 0)

    def test_board_owner_can_delete_a_foreign_task(self):
        task = Task.objects.create(
            board=self.board, title='By member', created_by=self.member,
        )
        self.client.force_authenticate(self.owner)
        url = reverse('task-detail', args=[task.id])
        self.assertEqual(
            self.client.delete(url).status_code,
            status.HTTP_204_NO_CONTENT,
        )

    def test_member_cannot_delete_a_foreign_task(self):
        self.client.force_authenticate(self.member)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Task.objects.count(), 1)

    def test_unknown_task_returns_404(self):
        self.client.force_authenticate(self.owner)
        response = self.client.delete(reverse('task-detail', args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_requires_authentication(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_str_returns_title(self):
        self.assertEqual(str(self.task), 'Write tests')


class RemovedMemberTests(TaskTestCase):
    """Covers what a user loses when they leave a board."""

    def setUp(self):
        super().setUp()
        self.own_task = Task.objects.create(
            board=self.board, title='Mine', created_by=self.member,
            assignee=self.member, reviewer=self.member,
        )
        self.board.members.set([self.owner])

    def test_removed_member_cannot_delete_the_own_task(self):
        self.client.force_authenticate(self.member)
        url = reverse('task-detail', args=[self.own_task.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Task.objects.filter(pk=self.own_task.pk).count(), 1)

    def test_removed_member_sees_no_assigned_tasks(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('task-assigned'))
        self.assertEqual(response.data, [])

    def test_removed_member_sees_no_reviewing_tasks(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('task-reviewing'))
        self.assertEqual(response.data, [])

    def test_outsider_cannot_probe_the_member_list(self):
        self.client.force_authenticate(self.other)
        response = self.client.post(reverse('task-create'), {
            'board': self.board.id,
            'title': 'Sneaky',
            'assignee_id': self.other.id,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DeletedUserTests(TaskTestCase):
    """Covers what happens to tasks when a user is deleted."""

    def test_tasks_survive_the_deletion_of_their_creator(self):
        task = Task.objects.create(
            board=self.board, title='By member', created_by=self.member,
        )
        self.member.delete()
        task.refresh_from_db()
        self.assertIsNone(task.created_by)
        self.assertEqual(task.board, self.board)

    def test_board_of_a_deleted_owner_is_removed(self):
        self.owner.delete()
        self.assertEqual(Board.objects.count(), 0)
        self.assertEqual(Task.objects.count(), 0)


class TaskListTests(TaskTestCase):
    """Covers the assigned-to-me and reviewing lists."""

    def test_assigned_list_shows_own_tasks(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('task-assigned'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.task.id)

    def test_assigned_list_is_empty_for_others(self):
        self.client.force_authenticate(self.other)
        response = self.client.get(reverse('task-assigned'))
        self.assertEqual(response.data, [])

    def test_reviewing_list_shows_tasks_to_review(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(reverse('task-reviewing'))
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.task.id)

    def test_assigned_list_requires_authentication(self):
        response = self.client.get(reverse('task-assigned'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reviewing_list_requires_authentication(self):
        response = self.client.get(reverse('task-reviewing'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BoardWithTasksTests(TaskTestCase):
    """Covers how tasks show up on their board."""

    def test_board_detail_lists_tasks_without_board_field(self):
        self.client.force_authenticate(self.owner)
        url = reverse('board-detail', args=[self.board.id])
        response = self.client.get(url)
        self.assertEqual(len(response.data['tasks']), 1)
        self.assertNotIn('board', response.data['tasks'][0])
        self.assertIn('comments_count', response.data['tasks'][0])

    def test_board_list_counts_tasks(self):
        Task.objects.create(
            board=self.board,
            title='High one',
            priority='high',
            created_by=self.owner,
        )
        self.client.force_authenticate(self.owner)
        response = self.client.get(reverse('board-list'))
        self.assertEqual(response.data[0]['ticket_count'], 2)
        self.assertEqual(response.data[0]['tasks_to_do_count'], 2)
        self.assertEqual(response.data[0]['tasks_high_prio_count'], 1)
