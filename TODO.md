# ERP E-Commerce Implementation Plan

## Phase 1: Foundation & Cleanup
1. [x] Remove legacy MySQL `database/` folder (dead code)
2. [x] Add proper database migrations (Flask-Migrate)
3. [x] Add config for PostgreSQL/SQLite switch
4. [x] Fix app factory to use single database source

## Phase 2: Core ERP Features - Missing
5. [x] Prevent out-of-stock sales in cart/checkout
6. [x] Add image upload endpoint for products
7. [x] Seed initial categories and sample products
8. [x] Add admin ability to create customers manually
9. [x] Complete user profile editing (address, phone, gender)

## Phase 3: Order & Invoice System
10. [x] Add order assignment to staff
11. [x] Add order filtering by status in admin
12. [x] Add "Print Invoice" button in UI
13. [x] Add invoice download/view endpoint

## Phase 4: Reporting System
14. [x] Sales report with date range filter
15. [x] Customer report (purchase history)
16. [x] Inventory report (stock levels)
17. [x] Profit estimation report

## Phase 5: Notification System
18. [x] Email notifications (order placed, shipped, low stock)
19. [x] In-app notification marking as read

## Phase 6: UI/UX Polish
20. [x] Add product images display in catalog
21. [x] Add search/filtering in product catalog
22. [x] Add responsive data tables with filters
23. [x] Polish admin panel WooCommerce-style

## Phase 7: Testing & Final
24. [ ] Test all user roles end-to-end
25. [ ] Verify PDF invoice generation
26. [ ] Test stock decrement on order

