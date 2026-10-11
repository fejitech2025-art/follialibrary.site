import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../views/HomeView.vue'
import ExploreView from '../views/ExploreView.vue'
import BookshelfView from '../views/BookshelfView.vue'
import PublishersView from '../views/PublishersView.vue'
import AccountView from '../views/AccountView.vue'
import NotificationsView from '../views/NotificationsView.vue'
import UploadResourceView from '../views/UploadResourceView.vue'
import EditProfileView from '../views/EditProfileView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ResourceDetailView from '../views/ResourceDetailView.vue'
import PublisherDetailView from '../views/PublisherDetailView.vue'
import BookClubView from '../views/BookClubView.vue'
import BookClubsView from '../views/BookClubsView.vue'
import CreateView from '../views/CreateView.vue'
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
import VerifyEmailView from '../views/VerifyEmailView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'
import PostDetailView from '../views/PostDetailView.vue'
import AboutView from '../views/AboutView.vue'

import { useAuth } from '../composables/useAuth'

const router = createRouter({
  history: createWebHistory(),

  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: {
        requiresAuth: true,
      },
    },

    {
      path: '/create',
      name: 'create',
      component: CreateView,
      meta: { requiresAuth: true },
    },

    {
      path: '/clubs',
      name: 'clubs',
      component: BookClubsView,
      meta: { requiresAuth: true },
    },

    {
      path: '/about',
      name: 'about',
      component: AboutView,
      meta: { requiresAuth: true },
    },

    {
      path: '/explore',
      name: 'explore',
      component: ExploreView,
      meta: {
        requiresAuth: true,
      },
    },

    {
      path: '/bookshelf',
      name: 'bookshelf',
      component: BookshelfView,
      meta: {
        requiresAuth: true,
      },
    },

    {
      path: '/publishers',
      name: 'publishers',
      component: PublishersView,
      meta: {
        requiresAuth: true,
      },
    },

    {
      path: '/account',
      name: 'account',
      component: AccountView,
      meta: {
        requiresAuth: true,
      },
    },

    {
      path: '/notifications',
      name: 'notifications',
      component: NotificationsView,
      meta: {
        requiresAuth: true,
      },
    },

    {
      path: '/upload',
      name: 'upload',
      component: UploadResourceView,
      meta: {
        requiresAuth: true,
      },
    },

    {
      path: '/account/edit',
      name: 'edit-profile',
      component: EditProfileView,
      meta: {
        requiresAuth: true,
      },
    },

    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: {
        guestOnly: true,
      },
    },

    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: {
        guestOnly: true,
      },
    },

    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: ForgotPasswordView,
      meta: { guestOnly: true },
    },

    {
      path: '/verify-email',
      name: 'verify-email',
      component: VerifyEmailView,
      meta: { guestOnly: true },
    },

    {
      path: '/reset-password/:uid/:token',
      name: 'reset-password',
      component: ResetPasswordView,
      meta: { guestOnly: true },
    },

    {
      path: '/resource/:id',
      name: 'resource-detail',
      component: ResourceDetailView,
      props: true,
      meta: {
        requiresAuth: true,
      },
    },

    {
      path: '/post/:id',
      name: 'post-detail',
      component: PostDetailView,
      props: true,
      meta: { requiresAuth: true },
    },

    {
      path: '/profile/:id',
      alias: '/publisher/:id',
      name: 'publisher-detail',
      component: PublisherDetailView,
      props: true,
      meta: {
        requiresAuth: true,
      },
    },

    {
      path: '/book-club/:id',
      name: 'book-club',
      component: BookClubView,
      props: true,
      meta: {
        requiresAuth: true,
      },
    },

    {
      path: '/search',
      name: 'search',
      component: ExploreView,
      meta: {
        requiresAuth: true,
      },
    },
  ],
})

/*
|--------------------------------------------------------------------------
| Authentication guard
|--------------------------------------------------------------------------
*/

router.beforeEach(async (to) => {
  const { user, initializeAuth } = useAuth()

  /*
 * Always wait for Django to restore the session
   * before making an authentication decision.
   */
  await initializeAuth()

  const isAuthenticated = !!user.value

  /*
   * Protected page without a session.
   */
  if (to.meta.requiresAuth && !isAuthenticated) {
    return {
      name: 'login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  /*
   * Login/register page while already authenticated.
   */
  if (to.meta.guestOnly && isAuthenticated) {
    return {
      name: 'home',
    }
  }

  return true
})

export default router
