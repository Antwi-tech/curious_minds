# Scheduler Database Documentation

## Overview

This database schema powers the **Scheduler System**, where **companies** create available time slots and **schools** can book those slots. An **admin** manages and verifies all accounts before they become active.

The schema is implemented in **MySQL** and uses foreign keys to maintain relational integrity.

---

## Database: `scheduler_db`

### 1. **Admins (`admin`)**

Stores platform administrators who manage approvals and oversee the system.

| Field           | Type         | Description                 |
| --------------- | ------------ | --------------------------- |
| `id`            | INT (PK)     | Unique admin ID             |
| `username`      | VARCHAR(50)  | Admin username (unique)     |
| `password_hash` | VARCHAR(255) | Hashed admin password       |
| `email`         | VARCHAR(100) | Admin email (unique)        |
| `created_at`    | TIMESTAMP    | Auto timestamp when created |

---

### 2. **Schools (`schools`)**

Stores school accounts that can register and book available company slots.

| Field            | Type         | Description                          |
| ---------------- | ------------ | ------------------------------------ |
| `school_id`      | INT (PK)     | Unique school ID                     |
| `school_name`    | VARCHAR(100) | Name of the school                   |
| `email`          | VARCHAR(100) | School login email (unique)          |
| `password_hash`  | VARCHAR(255) | Hashed password                      |
| `address`        | VARCHAR(255) | School address                       |
| `region`         | VARCHAR(100) | Region in Ghana                      |
| `contact_person` | VARCHAR(100) | Contact person’s full name           |
| `phone_number`   | VARCHAR(20)  | Contact phone number                 |
| `website`        | VARCHAR(100) | Optional school website              |
| `description`    | TEXT         | Description / notes about the school |
| `is_verified`    | BOOLEAN      | Set `TRUE` when approved by admin    |
| `created_at`     | TIMESTAMP    | Account creation time                |

---

### 3. **Companies (`companies`)**

Stores company accounts that create availability schedules for schools to book.

| Field            | Type         | Description                           |
| ---------------- | ------------ | ------------------------------------- |
| `company_id`     | INT (PK)     | Unique company ID                     |
| `company_name`   | VARCHAR(100) | Name of the company                   |
| `email`          | VARCHAR(100) | Company login email (unique)          |
| `password_hash`  | VARCHAR(255) | Hashed password                       |
| `industry_type`  | VARCHAR(100) | Type of industry (Tech, Health, etc.) |
| `description`    | TEXT         | Description of the company            |
| `address`        | VARCHAR(255) | Company address                       |
| `region`         | VARCHAR(100) | Region in Ghana                       |
| `contact_person` | VARCHAR(100) | Contact person’s full name            |
| `phone_number`   | VARCHAR(20)  | Contact phone number                  |
| `website`        | VARCHAR(100) | Optional company website              |
| `is_verified`    | BOOLEAN      | Set `TRUE` when approved by admin     |
| `created_at`     | TIMESTAMP    | Account creation time                 |

---

### 4. **Available Time Slots (`available_time`)**

Stores time slots created by companies for schools to book.

| Field            | Type     | Description                       |
| ---------------- | -------- | --------------------------------- |
| `schedule_id`    | INT (PK) | Unique schedule ID                |
| `company_id`     | INT (FK) | References `companies.company_id` |
| `start_datetime` | DATETIME | Slot start date and time          |
| `end_datetime`   | DATETIME | Slot end date and time            |
| `is_booked`      | BOOLEAN  | `TRUE` if already booked          |

🔗 **Relations:**

* A `company` can create many `available_time` slots.
* If a company is deleted, all their slots are deleted too (`ON DELETE CASCADE`).

---

### 5. **Bookings (`bookings`)**

Stores reservations made by schools against available slots.

| Field         | Type      | Description                             |
| ------------- | --------- | --------------------------------------- |
| `booking_id`  | INT (PK)  | Unique booking ID                       |
| `school_id`   | INT (FK)  | References `schools.school_id`          |
| `schedule_id` | INT (FK)  | References `available_time.schedule_id` |
| `status`      | ENUM      | `pending`, `confirmed`, or `cancelled`  |
| `created_at`  | TIMESTAMP | Booking creation time                   |

🔗 **Relations:**

* A `school` can book multiple slots.
* Each booking is tied to one `available_time` record.

---

## 🔗 Relationships Summary

* **Admin**: Manages everything but does not directly create bookings or slots.
* **Company**: Creates `available_time` slots → booked by schools.
* **School**: Registers and books slots from companies.
* **Bookings**: Link schools to company slots.

---

## ERD (Entity Relationship Diagram)
![Database diagram](ReadmeImages/database_diagram.png)

---

