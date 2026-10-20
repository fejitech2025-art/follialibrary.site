
<template>
  <MainLayout>
    <section class="profile-page">
      <!-- Loading -->
      <div v-if="loading" class="profile-loading">
        <LoaderCircle :size="23" class="spin" />
        <p>Loading profile...</p>
      </div>

      <!-- Error -->
      <div v-else-if="errorMessage" class="profile-error">
        <p>{{ errorMessage }}</p>
        <button class="primary-button" @click="loadProfile">Try again</button>
      </div>

      <!-- Profile -->
      <template v-else>
        <div class="profile-hero">
          <!-- Avatar -->
          <div class="profile-avatar-large">
            <UserAvatar :src="profile.avatar_url || profile.avatar" :alt="profile.display_name || 'Profile picture'" :icon-size="36" />
          </div>

          <!-- Main information -->
          <div class="profile-main">
            <div class="profile-title-row">
              <div>
                <h1>{{ profile.display_name || 'Follia User' }}</h1>
                <p>@{{ profile.username || 'user' }}</p>
              </div>

              <RouterLink to="/account/edit" class="edit-profile-button">
                <Pencil :size="17" />
                Edit profile
              </RouterLink>
            </div>

            <p class="profile-bio">
              {{ profile.bio || 'No bio added yet.' }}
            </p>

            <!-- Profile statistics -->
            <div class="profile-stats">
              <button type="button" @click="activeTab = 'Followers'"><Users :size="16" /><strong>{{ followerCount }}</strong><span>Followers</span></button>
              <button type="button" @click="activeTab = 'Following'"><UserRound :size="16" /><strong>{{ followingCount }}</strong><span>Following</span></button>
              <span class="profile-stat-item"><Heart :size="16" /><strong>{{ profile.like_count || 0 }}</strong><span>Likes</span></span>
            </div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="profile-tabs">
          <button
            v-for="tab in tabs"
            :key="tab"
            type="button"
            :class="{ active: activeTab === tab }"
            @click="activeTab = tab"
          >
            {{ tab }}

            <span v-if="tab === 'Resources'">
              {{ resources.length }}
            </span>

            <span v-else-if="tab === 'Saved'">
              {{ savedResources.length }}
            </span>

            <span v-else-if="tab === 'Followers'">
              {{ followerCount }}
            </span>

            <span v-else-if="tab === 'Following'">
              {{ followingCount }}
            </span>
          </button>
        </div>

        <div class="profile-content">
          <template v-if="activeTab === 'Posts'">
            <SectionHeader eyebrow="YOUR CONTENT" title="Posts you've shared" />
            <div v-if="postsLoading" class="content-loading"><LoaderCircle :size="22" class="spin" /><p>Loading your posts...</p></div>
            <div v-else-if="posts.length" class="posts-list"><FeedItemCard v-for="post in posts" :key="post.id" :item="{ ...post, kind: 'post' }" /></div>
            <div v-else class="empty-state"><div class="empty-icon"><MessageCircle :size="24" /></div><h2>No posts yet</h2><p>Your published images, videos, and posts will appear here.</p><RouterLink to="/create" class="primary-button">Create a post</RouterLink></div>
          </template>

          <!-- RESOURCES -->
          <template v-if="activeTab === 'Resources'">
            <SectionHeader
              eyebrow="YOUR CONTENT"
              title="Resources you've shared"
            />

            <div v-if="resourcesLoading" class="content-loading">
              <LoaderCircle :size="22" class="spin" />
              <p>Loading your resources...</p>
            </div>

            <div v-else-if="resources.length" class="resource-grid">
              <div
                v-for="resource in normalizedResources"
                :key="resource.id"
                class="owned-resource"
              >
                <ResourceCard :resource="resource" />

                <button
                  type="button"
                  class="delete-resource-button"
                  :class="{ deleting: deletingResourceId === resource.id }"
                  :disabled="deletingResourceId === resource.id"
                  :aria-label="`Delete ${resource.title}`"
                  :title="`Delete ${resource.title}`"
                  @click.stop="handleDeleteResource(resource)"
                >
                  <LoaderCircle
                    v-if="deletingResourceId === resource.id"
                    :size="17"
                    class="spin"
                  />
                  <Trash2 v-else :size="17" />
                </button>
              </div>
            </div>

            <div v-else class="empty-state">
              <div class="empty-icon">
                <BookOpen :size="24" />
              </div>

              <h2>No resources yet</h2>
              <p>Resources you upload will appear here.</p>

              <RouterLink to="/upload" class="primary-button">
                Upload resource
              </RouterLink>
            </div>

            <p v-if="resourceError" class="inline-error resource-error">
              {{ resourceError }}
            </p>
          </template>

          <!-- SAVED -->
          <template v-else-if="activeTab === 'Saved'">
            <SectionHeader
              eyebrow="YOUR LIBRARY"
              title="Saved resources"
            />

            <div v-if="savedLoading" class="content-loading">
              <LoaderCircle :size="22" class="spin" />
              <p>Loading your bookshelf...</p>
            </div>

            <div v-else-if="savedResources.length" class="resource-grid">
              <ResourceCard
                v-for="resource in normalizedSavedResources"
                :key="resource.id"
                :resource="resource"
              />
            </div>

            <div v-else class="empty-state">
              <div class="empty-icon">
                <Bookmark :size="24" />
              </div>

              <h2>Your bookshelf is empty</h2>
              <p>Resources you save will appear here.</p>

              <RouterLink to="/explore" class="primary-button">
                Explore resources
              </RouterLink>
            </div>
          </template>

          <!-- FOLLOWERS -->
          <template v-else-if="activeTab === 'Followers'">
            <div class="following-heading">
              <div>
                <SectionHeader
                  eyebrow="YOUR COMMUNITY"
                  title="Your followers"
                />

                <p class="following-description">
                  People who follow you on Follia.
                </p>
              </div>

              <span class="follow-count">
                {{ followerCount }}
                {{ followerCount === 1 ? 'person' : 'people' }}
              </span>
            </div>

            <div v-if="followersLoading" class="content-loading">
              <LoaderCircle :size="22" class="spin" />
              <p>Loading your followers...</p>
            </div>

            <div v-else-if="followers.length" class="following-list">
              <article
                v-for="person in followers"
                :key="person.id"
                class="follow-card"
              >
                <RouterLink
                  :to="{
                    name: 'publisher-detail',
                    params: { id: person.id },
                  }"
                  class="follow-person"
                >
                  <div class="follow-avatar">
                    <UserAvatar :src="person.avatar_url || person.avatar" :alt="person.display_name || person.username || 'Profile picture'" :icon-size="18" />
                  </div>

                  <div class="follow-person-info">
                    <strong>
                      {{ person.display_name || person.username || 'Follia User' }}
                    </strong>

                    <span v-if="person.username">
                      @{{ person.username }}
                    </span>

                    <p v-if="person.bio">
                      {{ person.bio }}
                    </p>
                  </div>
                </RouterLink>

                <div class="follow-actions">
                  <RouterLink
                    :to="{
                      name: 'publisher-detail',
                      params: { id: person.id },
                    }"
                    class="view-profile-button"
                  >
                    View profile
                  </RouterLink>
                </div>
              </article>
            </div>

            <div v-else class="empty-state">
              <div class="empty-icon">
                <Users :size="24" />
              </div>

              <h2>No followers yet</h2>
              <p>People who follow you will appear here.</p>

              <RouterLink to="/explore" class="primary-button">
                Discover publishers
              </RouterLink>
            </div>

            <p v-if="followError" class="inline-error">
              {{ followError }}
            </p>
          </template>

          <!-- FOLLOWING -->
          <template v-else-if="activeTab === 'Following'">
            <div class="following-heading">
              <div>
                <SectionHeader
                  eyebrow="YOUR COMMUNITY"
                  title="People you follow"
                />

                <p class="following-description">
                  Creators you follow on Follia.
                </p>
              </div>

              <span class="follow-count">
                {{ followingCount }}
                {{ followingCount === 1 ? 'person' : 'people' }}
              </span>
            </div>

            <div v-if="followingLoading" class="content-loading">
              <LoaderCircle :size="22" class="spin" />
              <p>Loading your following...</p>
            </div>

            <div v-else-if="following.length" class="following-list">
              <article
                v-for="person in following"
                :key="person.id"
                class="follow-card"
              >
                <RouterLink
                  :to="{
                    name: 'publisher-detail',
                    params: { id: person.id },
                  }"
                  class="follow-person"
                >
                  <div class="follow-avatar">
                    <UserAvatar :src="person.avatar_url || person.avatar" :alt="person.display_name || person.username || 'Profile picture'" :icon-size="18" />
                  </div>

                  <div class="follow-person-info">
                    <strong>
                      {{ person.display_name || person.username || 'Follia User' }}
                    </strong>

                    <span v-if="person.username">
                      @{{ person.username }}
                    </span>

                    <p v-if="person.bio">
                      {{ person.bio }}
                    </p>
                  </div>
                </RouterLink>

                <div class="follow-actions">
                  <RouterLink
                    :to="{
                      name: 'publisher-detail',
                      params: { id: person.id },
                    }"
                    class="view-profile-button"
                  >
                    View profile
                  </RouterLink>

                  <button
                    class="unfollow-button"
                    type="button"
                    :disabled="unfollowingId === person.id"
                    @click="handleUnfollow(person)"
                  >
                    {{
                      unfollowingId === person.id
                        ? 'Unfollowing...'
                        : 'Unfollow'
                    }}
                  </button>
                </div>
              </article>
            </div>

            <div v-else class="empty-state">
              <div class="empty-icon">
                <Users :size="24" />
              </div>

              <h2>No following yet</h2>

              <p>
                Find creators whose ideas and resources you want to follow.
              </p>

              <RouterLink to="/explore" class="primary-button">
                Discover publishers
              </RouterLink>
            </div>

            <p v-if="followError" class="inline-error">
              {{ followError }}
            </p>
          </template>
        </div>
      </template>
    </section>
  </MainLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import {
  Bookmark,
  BookOpen,
  LoaderCircle,
  Heart,
  MessageCircle,
  Pencil,
  Trash2,
  UserRound,
  Users,
} from 'lucide-vue-next'

import MainLayout from '../layouts/MainLayout.vue'
import SectionHeader from '../components/SectionHeader.vue'
import ResourceCard from '../components/ResourceCard.vue'
import FeedItemCard from '../components/FeedItemCard.vue'
import UserAvatar from '../components/UserAvatar.vue'

import { getMyProfile } from '../services/profileService'
import { getPublisherResources } from '../services/publisherService'
import { getMyBookmarks } from '../services/bookmarkService'
import { getPosts } from '../services/postService'

import {
  getFollowing,
  getFollowers,
  getFollowCounts,
  unfollowUser,
} from '../services/followService'

import { deleteResource } from '../services/resourceService'

const activeTab = ref('Resources')

const tabs = ['Resources', 'Posts', 'Saved', 'Followers', 'Following']

const profile = ref({
  id: '',
  display_name: '',
  username: '',
  location: '',
  bio: '',
  website: '',
  avatar_url: '',
  avatar: '',
})

const resources = ref([])
const posts = ref([])
const savedResources = ref([])
const following = ref([])
const followers = ref([])

/*
|--------------------------------------------------------------------------
| Directional follow counts
|--------------------------------------------------------------------------
|
| followingCount: People I follow.
| followerCount: People who follow me.
|
*/

const followingCount = ref(0)
const followerCount = ref(0)

const loading = ref(true)
const resourcesLoading = ref(false)
const postsLoading = ref(false)
const savedLoading = ref(false)
const followingLoading = ref(false)
const followersLoading = ref(false)

const errorMessage = ref('')
const followError = ref('')
const resourceError = ref('')

const unfollowingId = ref(null)
const deletingResourceId = ref(null)

/*
|--------------------------------------------------------------------------
| Normalize resources
|--------------------------------------------------------------------------
*/

function normalizeResource(resource) {
  if (!resource) {
    return null
  }

  return {
    ...resource,

    // Support either the serializer's URL field or the raw file field.
    cover: resource.cover_url || resource.cover,

    free: resource.is_free,

    author:
      resource.profiles?.display_name ||
      resource.profiles?.username ||
      'Unknown author',

    authorProfile: resource.profiles?.id
      ? `/publisher/${resource.profiles.id}`
      : null,
  }
}

const normalizedResources = computed(() => {
  return resources.value.map(normalizeResource).filter(Boolean)
})

const normalizedSavedResources = computed(() => {
  return savedResources.value
    .map((item) => normalizeResource(item.resources))
    .filter(Boolean)
})

async function loadPosts() {
  postsLoading.value = true
  try {
    posts.value = await getPosts({ author: profile.value.id })
  } catch (error) {
    console.error('My posts error:', error)
    posts.value = []
  } finally {
    postsLoading.value = false
  }
}

/*
|--------------------------------------------------------------------------
| Load profile
|--------------------------------------------------------------------------
*/

async function loadProfile() {
  loading.value = true
  errorMessage.value = ''

  try {
    const result = await getMyProfile()

    profile.value = result || {
      id: '',
      display_name: '',
      username: '',
      location: '',
      bio: '',
      website: '',
      avatar_url: '',
      avatar: '',
    }
  } catch (error) {
    console.error('Profile loading error:', error)

    errorMessage.value = error.message || 'Unable to load your profile.'
  } finally {
    loading.value = false
  }

  if (!profile.value?.id) {
    return
  }

  await Promise.all([
    loadResources(),
    loadPosts(),
    loadSavedResources(),
    loadFollowing(),
    loadFollowers(),
    loadFollowCounts(),
  ])
}

/*
|--------------------------------------------------------------------------
| Load my resources
|--------------------------------------------------------------------------
*/

async function loadResources() {
  resourcesLoading.value = true
  resourceError.value = ''

  try {
    resources.value = await getPublisherResources(profile.value.id)
  } catch (error) {
    console.error('My resources error:', error)

    resources.value = []
    resourceError.value = 'Could not load your resources. Please try again.'
  } finally {
    resourcesLoading.value = false
  }
}

/*
|--------------------------------------------------------------------------
| Delete my resource
|--------------------------------------------------------------------------
*/

async function handleDeleteResource(resource) {
  if (!resource?.id || deletingResourceId.value) {
    return
  }

  const confirmed = window.confirm(
    `Delete "${resource.title}"? This cannot be undone.`,
  )

  if (!confirmed) {
    return
  }

  deletingResourceId.value = resource.id
  resourceError.value = ''

  try {
    await deleteResource(resource.id)

    resources.value = resources.value.filter(
      (item) => item.id !== resource.id,
    )
  } catch (error) {
    console.error('Delete resource error:', error)

    resourceError.value =
      error?.message || 'Could not delete the resource. Please try again.'
  } finally {
    deletingResourceId.value = null
  }
}

/*
|--------------------------------------------------------------------------
| Load saved resources
|--------------------------------------------------------------------------
*/

async function loadSavedResources() {
  savedLoading.value = true

  try {
    savedResources.value = await getMyBookmarks()
  } catch (error) {
    console.error('Saved resources error:', error)
    savedResources.value = []
  } finally {
    savedLoading.value = false
  }
}

/*
|--------------------------------------------------------------------------
| Load outgoing following
|--------------------------------------------------------------------------
*/

async function loadFollowing() {
  followingLoading.value = true
  followError.value = ''

  try {
    following.value = await getFollowing()
  } catch (error) {
    console.error('Following loading error:', error)

    followError.value = 'Could not load your following. Please try again.'
    following.value = []
  } finally {
    followingLoading.value = false
  }
}

/*
|--------------------------------------------------------------------------
| Load incoming followers
|--------------------------------------------------------------------------
*/

async function loadFollowers() {
  followersLoading.value = true

  try {
    followers.value = await getFollowers()
  } catch (error) {
    console.error('Followers loading error:', error)

    followers.value = []

    if (!followError.value) {
      followError.value = 'Could not load your followers. Please try again.'
    }
  } finally {
    followersLoading.value = false
  }
}

/*
|--------------------------------------------------------------------------
| Load directional follow counts
|--------------------------------------------------------------------------
*/

async function loadFollowCounts() {
  try {
    const counts = await getFollowCounts()

    followingCount.value = counts.followingCount
    followerCount.value = counts.followerCount
  } catch (error) {
    console.error('Follow counts error:', error)

    followingCount.value = 0
    followerCount.value = 0
  }
}

/*
|--------------------------------------------------------------------------
| Unfollow
|--------------------------------------------------------------------------
*/

async function handleUnfollow(person) {
  if (unfollowingId.value) {
    return
  }

  const confirmed = window.confirm(
    `Unfollow ${person.display_name || person.username || 'this user'}?`,
  )

  if (!confirmed) {
    return
  }

  unfollowingId.value = person.id
  followError.value = ''

  try {
    await unfollowUser(person.id)

    following.value = following.value.filter(
      (follow) => follow.id !== person.id,
    )

    followingCount.value = Math.max(0, followingCount.value - 1)
  } catch (error) {
    console.error('Unfollow error:', error)

    followError.value = 'Could not update this follow yet. Please try again.'
  } finally {
    unfollowingId.value = null
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-page {
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
  padding: 32px 24px 120px;
  color: var(--text-main);
}

.profile-loading,
.profile-error,
.content-loading {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
  text-align: center;
}

.profile-error {
  color: #b42318;
}

.profile-hero {
  display: flex;
  align-items: flex-start;
  gap: 28px;
  padding: 30px;
  border: 1px solid var(--border-color);
  border-radius: 26px;
  background: var(--card-bg);
}

.profile-avatar-large {
  width: 104px;
  height: 104px;
  flex: 0 0 104px;
  display: grid;
  place-items: center;
  overflow: hidden;
  border-radius: 28px;
  background: #eef0ff;
  color: #4f5bd5;
  font-size: 30px;
  font-weight: 800;
}

.profile-avatar-large img,
.follow-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-main {
  min-width: 0;
  flex: 1;
}

.profile-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.profile-title-row h1 {
  margin: 0;
  font-size: clamp(26px, 4vw, 36px);
  letter-spacing: -0.04em;
}

.profile-title-row p {
  margin: 6px 0 0;
  color: var(--text-tertiary);
  font-size: 13px;
}

.edit-profile-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-shrink: 0;
  padding: 11px 14px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--card-bg);
  color: var(--text-main);
  font-size: 13px;
  text-decoration: none;
}

.edit-profile-button:hover,
.view-profile-button:hover {
  background: var(--surface-soft);
}

.profile-bio {
  margin: 18px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

/* PROFILE STATS */

.profile-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 28px;
  margin-top: 24px;
}

.profile-stats button,
.profile-stat-item {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
}

.profile-stats button {
  cursor: pointer;
}

.profile-stats strong {
  font-size: 19px;
  font-weight: 800;
}

.profile-stats span {
  color: var(--text-secondary);
  font-size: 13px;
}

.profile-stat-item {
  cursor: default;
}

.profile-stats button > svg,
.profile-stat-item > svg { color:var(--text-tertiary); flex:0 0 auto; }
.posts-list { display:grid; gap:13px; max-width:680px; margin-top:24px; }

/* TABS */

.profile-tabs {
  display: flex;
  gap: 26px;
  margin-top: 36px;
  border-bottom: 1px solid var(--border-color);
}

.profile-tabs button {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 0 0 14px;
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--text-tertiary);
  font: inherit;
  font-size: 14px;
  cursor: pointer;
}

.profile-tabs button.active {
  border-bottom-color: #4f5bd5;
  color: var(--text-main);
  font-weight: 700;
}

.profile-tabs button span {
  color: var(--text-tertiary);
  font-size: 12px;
}

/* CONTENT */

.profile-content {
  padding-top: 30px;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
  margin-top: 24px;
}

/* OWN RESOURCE DELETE */

.owned-resource {
  position: relative;
  min-width: 0;
}

.delete-resource-button {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 20;
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border: 1px solid var(--border-color);
  border-radius: 11px;
  background: var(--card-bg);
  color: #a33b35;
  box-shadow: 0 8px 22px var(--shadow-color);
  cursor: pointer;
  opacity: 0;
  transform: translateY(-4px) scale(0.94);
  transition:
    opacity 0.18s ease,
    transform 0.18s ease,
    background 0.18s ease,
    color 0.18s ease;
}

.owned-resource:hover .delete-resource-button,
.delete-resource-button:focus-visible {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.delete-resource-button:hover:not(:disabled) {
  background: #fff1ef;
  color: #c03932;
}

.delete-resource-button:disabled {
  cursor: wait;
  opacity: 1;
  transform: translateY(0) scale(1);
}

.delete-resource-button.deleting {
  pointer-events: none;
}

.resource-error {
  margin-top: 18px;
}

/* EMPTY STATES */

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 54px 24px;
  border: 1px dashed var(--border-color);
  border-radius: 22px;
  text-align: center;
}

.empty-icon {
  width: 50px;
  height: 50px;
  display: grid;
  place-items: center;
  margin-bottom: 16px;
  border-radius: 16px;
  background: var(--surface-soft);
  color: var(--text-secondary);
}

.empty-state h2 {
  margin: 0;
  font-size: 19px;
}

.empty-state > p {
  max-width: 420px;
  margin: 9px 0 20px;
  color: var(--text-tertiary);
  font-size: 14px;
  line-height: 1.6;
}

.primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 11px 16px;
  border: 0;
  border-radius: 12px;
  background: var(--primary-bg);
  color: var(--primary-text);
  font: inherit;
  font-size: 13px;
  text-decoration: none;
  cursor: pointer;
}

/* FOLLOWS */

.following-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.following-description {
  margin: 8px 0 0;
  color: var(--text-tertiary);
  font-size: 13px;
}

.follow-count {
  flex-shrink: 0;
  padding: 8px 11px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  color: var(--text-secondary);
  font-size: 12px;
}

.following-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 24px;
}

.follow-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background: var(--card-bg);
}

.follow-person {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
  color: inherit;
  text-decoration: none;
}

.follow-avatar {
  width: 54px;
  height: 54px;
  flex: 0 0 54px;
  display: grid;
  place-items: center;
  overflow: hidden;
  border-radius: 17px;
  background: #eef0ff;
  color: #4f5bd5;
  font-size: 18px;
  font-weight: 800;
}

.follow-person-info {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.follow-person-info strong {
  overflow: hidden;
  color: var(--text-main);
  font-size: 14px;
  text-overflow: ellipsis;
}

.follow-person-info > span {
  color: var(--text-tertiary);
  font-size: 12px;
}

.follow-person-info p {
  max-width: 460px;
  margin: 2px 0 0;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.follow-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.view-profile-button,
.unfollow-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 9px 12px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: var(--card-bg);
  color: var(--text-main);
  font: inherit;
  font-size: 12px;
  text-decoration: none;
  cursor: pointer;
}

.unfollow-button {
  color: #a33b35;
}

.unfollow-button:hover:not(:disabled) {
  background: #fff4f2;
}

.unfollow-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.inline-error {
  margin-top: 16px;
  color: #b42318;
  font-size: 13px;
}

/* ANIMATION */

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* RESPONSIVE */

@media (max-width: 900px) {
  .resource-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .profile-hero {
    align-items: flex-start;
  }

  .follow-card {
    align-items: flex-start;
    flex-direction: column;
  }

  .follow-actions {
    width: 100%;
  }

  .follow-actions > * {
    flex: 1;
  }
}

@media (max-width: 600px) {
  .profile-page {
    padding: 22px 16px 110px;
  }

  .profile-hero {
    flex-direction: column;
    padding: 22px;
    border-radius: 22px;
  }

  .profile-avatar-large {
    width: 82px;
    height: 82px;
    flex-basis: 82px;
    border-radius: 23px;
    font-size: 24px;
  }

  .profile-main {
    width: 100%;
  }

  .profile-title-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .profile-stats {
    gap: 18px;
  }

  .profile-stats button,
  .profile-stat-item {
    flex-direction: column;
    gap: 3px;
  }

  .profile-tabs {
    gap: 20px;
    overflow-x: auto;
  }

  .profile-tabs button {
    flex-shrink: 0;
  }

  .resource-grid {
    grid-template-columns: 1fr;
  }

  /*
   * On touch devices there is no hover,
   * so keep the delete button visible.
   */
  .delete-resource-button {
    opacity: 1;
    transform: translateY(0) scale(1);
  }

  .following-heading {
    flex-direction: column;
  }

  .follow-person {
    width: 100%;
  }

  .follow-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
