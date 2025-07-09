import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

class AuthService {
  login(email, password, role) {
    return axios
      .post(API_URL + '/login', {
        email,
        password,
        role
      })
      .then(response => {
        if (response.data.user) {
          localStorage.setItem('user', JSON.stringify(response.data.user));
        }
        return response.data;
      });
  }

  logout() {
    localStorage.removeItem('user');
    return axios.post(API_URL + '/logout');
  }

  getCurrentUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  }

  isAuthenticated() {
    const user = this.getCurrentUser();
    return !!user;
  }

  hasRole(requiredRole) {
    const user = this.getCurrentUser();
    return user && user.role === requiredRole;
  }

  hasAnyRole(requiredRoles) {
    const user = this.getCurrentUser();
    return user && requiredRoles.includes(user.role);
  }
}

export default new AuthService();