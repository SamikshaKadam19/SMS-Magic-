import unittest
from flask import json
from your_app_module import app, db, User, Company, Client, ClientUser

class YourAppTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_user_list_resource(self):
        # Test the UserListResource endpoint
        response = self.app.get('/users')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertTrue('users' in data)

    def test_user_replace_resource(self):
        # Test the UserReplaceResource endpoint
        user = User(username='test_user')
        db.session.add(user)
        db.session.commit()

        updated_data = {'username': 'updated_user'}
        response = self.app.put(f'/users/{user.id}', data=json.dumps(updated_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['message'], 'User updated successfully')

    def test_client_list_resource(self):
        # Test the ClientListResource endpoint
        user = User(username='admin', role='ROLE_ADMIN')
        db.session.add(user)
        db.session.commit()

        auth_token = self.get_auth_token('admin', 'your_secret_key')

        client_data = {
            'name': 'TestClient',
            'email': 'test@example.com',
            'phone': '123456789',
            'user_id': user.id,
            'company_id': 1  # Adjust company_id based on your test data
        }

        response = self.app.post('/clients', data=json.dumps(client_data), content_type='application/json',
                                 headers={'Authorization': f'Bearer {auth_token}'})
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['message'], 'Client created successfully')

    def test_client_field_resource(self):
        # Test the ClientFieldResource endpoint
        client = Client(name='TestClient', email='test@example.com', phone='123456789', user_id=1, company_id=1)
        db.session.add(client)
        db.session.commit()

        updated_data = {'name': 'UpdatedClient'}
        response = self.app.patch(f'/clients/{client.id}', data=json.dumps(updated_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['message'], 'Client field(s) updated successfully')

    def get_auth_token(self, username, secret_key):
        # Helper method to obtain authentication token for testing
        response = self.app.post('/login', data=dict(username=username, password=secret_key))
        data = json.loads(response.data.decode('utf-8'))
        return data.get('access_token')

if __name__ == '__main__':
    unittest.main()
