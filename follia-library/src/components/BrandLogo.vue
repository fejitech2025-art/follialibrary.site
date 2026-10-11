<script setup>
import logo from '../assets/logo/image.png'
</script>

<template>
  <img class="brand-logo" :src="logo" alt="" />
</template>

<style scoped>
.brand-logo {
  display: block;
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  object-fit: contain;
}
</style>
