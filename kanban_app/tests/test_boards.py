from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import User
from kanban_app.models import Board

PASSWORD = 'kanmind-4711!'


class BoardListTests(APITestCase):
    """Covers GET and POST on /api/boards/."""

    def setUp(self):
        self.url = reverse('board-list')
        self.owner = User.objects.create_user('a@example.com', 'A', PASSWORD)
        self.member = User.objects.create_user('b@example.com', 'B', PASSWORD)
        self.other = User.objects.create_user('c@example.com', 'C', PASSWORD)
        self.board = Board.objects.create(title='Sprint', owner=self.owner)
        self.board.members.set([self.owner, self.member])

    def test_list_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_sees_the_board_with_counters(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['member_count'], 2)
        self.assertEqual(response.data[0]['owner_id'], self.owner.id)

    def test_member_sees_the_board_with_the_same_counters(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['member_count'], 2)
        self.assertEqual(response.data[0]['owner_id'], self.owner.id)

    def test_list_does_not_leak_member_ids(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.url)
        self.assertNotIn('members', response.data[0])

    def test_outsider_sees_no_board(self):
        self.client.force_authenticate(self.other)
        response = self.client.get(self.url)
        self.assertEqual(response.data, [])

    def test_create_board_returns_201(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.url, {
            'title': 'New board',
            'members': [self.member.id],
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New board')
        self.assertEqual(response.data['member_count'], 2)

    def test_creator_becomes_owner_and_member(self):
        self.client.force_authenticate(self.other)
        response = self.client.post(self.url, {'title': 'Solo'})
        board = Board.objects.get(pk=response.data['id'])
        self.assertEqual(board.owner, self.other)
        self.assertIn(self.other, board.members.all())

    def test_create_without_title_returns_400(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.url, {'members': []})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_requires_authentication(self):
        response = self.client.post(self.url, {'title': 'Nope'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BoardDetailTests(APITestCase):
    """Covers GET, PATCH and DELETE on /api/boards/{id}/."""

    def setUp(self):
        self.owner = User.objects.create_user('a@example.com', 'A', PASSWORD)
        self.member = User.objects.create_user('b@example.com', 'B', PASSWORD)
        self.other = User.objects.create_user('c@example.com', 'C', PASSWORD)
        self.board = Board.objects.create(title='Sprint', owner=self.owner)
        self.board.members.set([self.owner, self.member])
        self.url = reverse('board-detail', args=[self.board.id])

    def test_member_can_read_the_board(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['owner_id'], self.owner.id)
        self.assertEqual(len(response.data['members']), 2)
        self.assertEqual(response.data['tasks'], [])

    def test_outsider_gets_403(self):
        self.client.force_authenticate(self.other)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unknown_board_returns_404(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(reverse('board-detail', args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unknown_board_without_token_returns_401(self):
        response = self.client.get(reverse('board-detail', args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_read_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_can_patch_title(self):
        self.client.force_authenticate(self.member)
        response = self.client.patch(self.url, {'title': 'Renamed'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Renamed')
        self.assertEqual(response.data['owner_data']['id'], self.owner.id)
        self.assertEqual(len(response.data['members_data']), 2)

    def test_patch_replaces_the_member_list(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(self.url, {'members': [self.other.id]})
        emails = [m['email'] for m in response.data['members_data']]
        self.assertIn('c@example.com', emails)
        self.assertIn('a@example.com', emails)
        self.assertNotIn('b@example.com', emails)

    def test_patch_with_unknown_member_returns_400(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(self.url, {'members': [9999]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_outsider_cannot_patch(self):
        self.client.force_authenticate(self.other)
        response = self.client.patch(self.url, {'title': 'Hacked'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_delete(self):
        self.client.force_authenticate(self.owner)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Board.objects.count(), 0)

    def test_member_cannot_delete(self):
        self.client.force_authenticate(self.member)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Board.objects.count(), 1)

    def test_delete_requires_authentication(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_is_not_allowed(self):
        self.client.force_authenticate(self.owner)
        response = self.client.put(self.url, {'title': 'Nope'})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_str_returns_title(self):
        self.assertEqual(str(self.board), 'Sprint')
