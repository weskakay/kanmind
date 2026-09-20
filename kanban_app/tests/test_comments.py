from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import User
from kanban_app.models import Board, Comment, Task

PASSWORD = 'kanmind-4711!'


class CommentTestCase(APITestCase):
    """A task on a shared board with one existing comment."""

    def setUp(self):
        self.owner = User.objects.create_user('a@example.com', 'Ann', PASSWORD)
        self.member = User.objects.create_user(
            'b@example.com', 'Ben', PASSWORD,
        )
        self.other = User.objects.create_user('c@example.com', 'Cem', PASSWORD)
        self.board = Board.objects.create(title='Sprint', owner=self.owner)
        self.board.members.set([self.owner, self.member])
        self.task = Task.objects.create(
            board=self.board, title='Write docs', created_by=self.owner,
        )
        self.comment = Comment.objects.create(
            task=self.task, author=self.member, content='First note',
        )
        self.list_url = reverse('comment-list', args=[self.task.id])


class CommentListTests(CommentTestCase):
    """Covers GET and POST on /api/tasks/{id}/comments/."""

    def test_member_sees_the_comments(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['author'], 'Ben')
        self.assertEqual(response.data[0]['content'], 'First note')

    def test_comments_are_sorted_oldest_first(self):
        Comment.objects.create(
            task=self.task, author=self.owner, content='Second note',
        )
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.list_url)
        contents = [entry['content'] for entry in response.data]
        self.assertEqual(contents, ['First note', 'Second note'])

    def test_outsider_gets_403(self):
        self.client.force_authenticate(self.other)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unknown_task_returns_404(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(reverse('comment-list', args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_requires_authentication(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_can_write_a_comment(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.list_url, {'content': 'Looks good'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['author'], 'Ann')
        self.assertEqual(Comment.objects.count(), 2)

    def test_empty_content_returns_400(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.list_url, {'content': ''})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Comment.objects.count(), 1)

    def test_missing_content_returns_400(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.list_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_outsider_cannot_write(self):
        self.client.force_authenticate(self.other)
        response = self.client.post(self.list_url, {'content': 'Hello'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Comment.objects.count(), 1)

    def test_author_cannot_be_faked(self):
        self.client.force_authenticate(self.owner)
        self.client.post(self.list_url, {
            'content': 'Mine', 'author': self.member.id,
        })
        self.assertEqual(Comment.objects.last().author, self.owner)

    def test_write_requires_authentication(self):
        response = self.client.post(self.list_url, {'content': 'Hello'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CommentDeleteTests(CommentTestCase):
    """Covers DELETE on /api/tasks/{id}/comments/{cid}/."""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'comment-detail', args=[self.task.id, self.comment.id],
        )

    def test_author_can_delete(self):
        self.client.force_authenticate(self.member)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)

    def test_board_owner_cannot_delete_a_foreign_comment(self):
        self.client.force_authenticate(self.owner)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Comment.objects.count(), 1)

    def test_outsider_cannot_delete(self):
        self.client.force_authenticate(self.other)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unknown_comment_returns_404(self):
        self.client.force_authenticate(self.member)
        url = reverse('comment-detail', args=[self.task.id, 9999])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_comment_of_another_task_returns_404(self):
        other_task = Task.objects.create(
            board=self.board, title='Other', created_by=self.owner,
        )
        url = reverse('comment-detail', args=[other_task.id, self.comment.id])
        self.client.force_authenticate(self.member)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_requires_authentication(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CommentAccessTests(CommentTestCase):
    """Covers who reaches the comments of a task."""

    def test_status_order_stays_right_for_a_bad_body(self):
        self.client.force_authenticate(self.other)
        response = self.client.post(self.list_url, {'content': ''})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unknown_task_wins_over_a_bad_body(self):
        self.client.force_authenticate(self.owner)
        url = reverse('comment-list', args=[9999])
        response = self.client.post(url, {'content': ''})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_removed_member_cannot_delete_the_own_comment(self):
        self.board.members.set([self.owner])
        self.client.force_authenticate(self.member)
        url = reverse(
            'comment-detail', args=[self.task.id, self.comment.id],
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Comment.objects.count(), 1)

    def test_outsider_gets_403_for_an_unknown_comment(self):
        self.client.force_authenticate(self.other)
        url = reverse('comment-detail', args=[self.task.id, 9999])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_board_owner_outside_members_may_read(self):
        self.board.members.set([self.member])
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CommentModelTests(CommentTestCase):
    """Covers the comment model itself."""

    def test_str_names_author_and_task(self):
        self.assertEqual(str(self.comment), 'b@example.com on Write docs')


class CommentCountTests(CommentTestCase):
    """Covers the comment counter on tasks."""

    def test_task_counts_its_comments(self):
        self.client.force_authenticate(self.owner)
        url = reverse('board-detail', args=[self.board.id])
        response = self.client.get(url)
        self.assertEqual(response.data['tasks'][0]['comments_count'], 1)

    def test_comments_disappear_with_their_task(self):
        self.task.delete()
        self.assertEqual(Comment.objects.count(), 0)
