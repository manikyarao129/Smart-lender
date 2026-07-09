# Smart Lender

## Overview

Smart Lender is a loan management application designed to simplify the lending process for borrowers and lenders. The platform enables users to apply for loans, manage repayments, track loan status, and securely store financial records through an intuitive interface.

## Features

* User registration and secure authentication
* Loan application and approval workflow
* Loan status tracking
* EMI and repayment management
* Payment history
* User profile management
* Admin dashboard for loan monitoring
* Secure data storage
* Responsive user interface

## Technology Stack

### Frontend

* React.js
* HTML5
* CSS3
* JavaScript

### Backend

* Node.js
* Express.js

### Database

* MongoDB

### Authentication

* JSON Web Tokens (JWT)
* bcrypt

## Project Structure

```
smart-lender/
├── client/
│   ├── src/
│   ├── public/
│   └── package.json
├── server/
│   ├── controllers/
│   ├── models/
│   ├── routes/
│   ├── middleware/
│   ├── config/
│   └── server.js
├── README.md
└── package.json
```

## Installation

### Clone the repository

```bash
git clone <repository-url>
cd smart-lender
```

### Install dependencies

Backend:

```bash
cd server
npm install
```

Frontend:

```bash
cd client
npm install
```

### Configure environment variables

Create a `.env` file in the server directory:

```env
PORT=5000
MONGO_URI=your_mongodb_connection_string
JWT_SECRET=your_jwt_secret
```

### Run the application

Backend:

```bash
npm start
```

Frontend:

```bash
npm start
```

The application will be available at:

* Frontend: `http://localhost:3000`
* Backend: `http://localhost:5000`

## API Endpoints

### Authentication

* `POST /api/auth/register`
* `POST /api/auth/login`

### Loans

* `GET /api/loans`
* `POST /api/loans/apply`
* `GET /api/loans/:id`
* `PUT /api/loans/:id`
* `DELETE /api/loans/:id`

### Users

* `GET /api/users/profile`
* `PUT /api/users/profile`

## Security

* Password hashing using bcrypt
* JWT-based authentication
* Protected API routes
* Input validation
* Environment-based configuration

## Future Enhancements

* Credit score integration
* Email and SMS notifications
* Payment gateway integration
* Document upload and verification
* Analytics dashboard
* Mobile application support

## Contributing

Contributions are welcome. Please fork the repository, create a feature branch, commit your changes, and submit a pull request.

## License

This project is licensed under the MIT License.

## Author

Ch Manikya rao
