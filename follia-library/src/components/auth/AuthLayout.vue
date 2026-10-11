<template>
  <div class="auth-page">
    <div class="auth-visual">
      <div class="auth-brand">
        <BrandLogo />
        <span>Follia Library</span>
      </div>

      <div class="auth-visual-content">
        <p class="auth-eyebrow">FOLLIA LIBRARY</p>

        <h1>
          A place for
          <span>knowledge to move.</span>
        </h1>

        <p>
          Discover, share and collect resources created for students, educators and curious minds.
        </p>
      </div>

      <div class="auth-floating-card auth-card-one">
        <span>01</span>
        <strong>Discover resources</strong>
      </div>

      <div class="auth-floating-card auth-card-two">
        <span>02</span>
        <strong>Share what you know</strong>
      </div>

      <div class="auth-visual-footer">
        <span>© Follia</span>
        <span>Discover anything.</span>
      </div>
    </div>

    <div class="auth-form-side">
      <div class="auth-form-container">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
import BrandLogo from '../BrandLogo.vue'
</script>
