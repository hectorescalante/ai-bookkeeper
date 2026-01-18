import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "documents",
    component: () => import("@/views/DocumentsView.vue"),
    meta: { title: "Documents" },
  },
  {
    path: "/bookings",
    name: "bookings",
    component: () => import("@/views/BookingsView.vue"),
    meta: { title: "Bookings" },
  },
  {
    path: "/bookings/:id",
    name: "booking-detail",
    component: () => import("@/views/BookingDetailView.vue"),
    meta: { title: "Booking Detail" },
  },
  {
    path: "/reports",
    name: "reports",
    component: () => import("@/views/ReportsView.vue"),
    meta: { title: "Reports" },
  },
  {
    path: "/settings",
    name: "settings",
    component: () => import("@/views/SettingsView.vue"),
    meta: { title: "Settings" },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
