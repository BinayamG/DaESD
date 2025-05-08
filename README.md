# UniHub - (Group 38)

## Group Members:

- **Indivar Mendiratta**
- **Binayam Gurung**
- **Sumanth Kasthuri**
- **Selinsu Vural**
- **Zheng Yin**

UniHub is an online platform designed to enhance discovery and engagement between students, by intuitively integrating functionalities such as the creation of communities, events and posts. Furthermore, a student is able to personalise their own account with their academic achievements and interests, allowing engagement and discovery between other students.

## Functionalities

- **User Profiles**: The user can create and customise their profile with academic achievements, interests and a changeable profile picture etc.
- **Community Engagement and Management**: The user can join and create communities (If approved by a super_user), allowing them to view community-only events and posts. The commmunity leader can view and manage the members in the community. 
- **Event Joining and Management**: The user can register or create community only/ campus events (only if community leader) that have the relevant information provided.
- **Notifications**: The user is notified on  their interactions with the system, for example, the creation of posts, or friend requests etc.
- **Friendship functionality**: The user can send friend requests, and the receiver can either reject or accept the request. Friendship status can also be managed and the interests and academic achievements of friends can be viewed.
- **Posts and Comments Management**: The user can add and delete their respective comments and posts to respective communities, allowing engagement and discussion for users. Furthermore community leaders have full management of comments and posts and can moderate it as deemed.
- **Admin**: The admin/super_user can approve and disapprove community creation requests and view every event without membership.



## Pipeline

- **Sign up and Login**: Create an account to access the main functionalities and login with respective details.
- **Explore Communities**: Search, create or join communities that match your interests.
- **Approval**: Using an admin/super_user account, approve the creation of the community or reject with a rejection reason.
- **Create Events**: Create events for your community.
- **Add Friends**: Search for users in the main dashboard to friend them, you can also view their interests and academic achievements here.
- **Engage**: Post updates, comment, and interact with other members.

## Folder Structure

- `myapp/`: Contains the core application logic with respective folders.
  - `models.py`: Defines database models for users, communities, events, posts, comments, and notifications.
  - `views.py`: Handles the logic for rendering templates and processing user actions.
  - `urls.py`: Maps URLs to their respective views.
- `templates/`: HTML templates for the frontend, including:
  - `accounts/main.html`: The main dashboard for users that include the communities and respective functionalities.
  - `postList.html`: Displays posts within a community.
  - `home.html`: The first initial page before logging in or signing up
- `static/`: Static files including CSS, JavaScript, and images.
- `media/`: Uploaded media files (e.g., profile images, post attachments in the Django WEB APP).
- `requirements.txt`: File that holds the Python dependencies for the project.
- `manage.py`: Django's command-line utility for administrative tasks such as makemigrations and migrate.
- `docker-compose.yml` and `Dockerfile`: Configuration files for containerization.

## Initializing Docker

To run the project using Docker, follow these steps:

1. Ensure Docker is installed and running on your system.
2. Navigate to the project directory where the `docker-compose.yml` file is located:
   cd DaESD\myproject
3. Build and start the Docker containers:
   docker-compose up --build
4. Access the application at `http://127.0.0.1:8000/` in your web browser.
5. To stop the containers, press `Ctrl+C` in the terminal or run:
   docker-compose down
