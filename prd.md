# Melvin: Product Requirements Document (PRD)

## 1. Project Overview
**Melvin** is a modular, general-purpose Discord bot designed to provide a comprehensive suite of tools for server management, engagement, and utility. Inspired by the flexibility of YAGPDB, Melvin allows server administrators to toggle and configure specific modules to tailor the bot's functionality to their community's unique needs.

## 2. Core Philosophy & Design
*   **Modularity First:** Every major feature is a standalone module that can be enabled, disabled, or configured independently.
*   **Minimalist Aesthetics:** Following the [Melvin Design System](file:///c:/Users/saltgranule/Desktop/Melvin/mds.md), all user-facing interfaces (web dashboard and bot responses where possible) will adhere to a flat, clean, and lowercase-only aesthetic.
*   **Simplicity:** No unnecessary clutter. Direct and modern interaction.

---

## 3. Modular Architecture
The bot will be built on a core framework that handles:
*   Module registration and lifecycle management.
*   Configuration storage (SQLAlchemy)
*   Permission handling.
*   Inter-module communication (events).

---

## 4. Feature Requirements (Target Areas)

### 4.1. Base (Core)
*   **help command:** dynamic help system that only displays enabled modules.
*   **slash commands:** support for modern slash commands.
*   **module toggle:** server owners can enable/disable modules via command or dashboard.

### 4.2. Moderation
*   **standard actions:** kick, ban (temp/perm), mute (discord timeout), warn.
*   **automatic moderation:** word filtering, anti-spam (message frequency), and link protection.
*   **case tracking:** detailed logging of moderator actions with unique case ids. Instead of relying on permissions for actions, the moderators can configure certain roles to be able to complete certain actions, bypassing permissions via dashboard

### 4.3. FrogBoard (Starboard)
*   **engagement tracking:** users can "react" to messages (default: 🐸) to highlight them in a specific channel.
*   **configurable thresholds:** set the number of reactions required to "board" a message.
*   **embed style:** minimalist, flat embeds following the design system. image + gif support for videos, and images

### 4.4. Economy (seasonal)
*   **currency system:** virtual currency (e.g., "flies").
*   **commands:** balance, pay, daily rewards.
*   **shop:** configurable item shop for roles or custom perks.
*   **leaderboards:** global or server-specific rankings. users can configure their economy module to be global, or server specific, with server specific offering more customization in terms of how currency is earned and spent.

### 4.5. Levels (XP System)
*   **activity reward:** xp granted for messaging and voice activity.
*   **level up notifications:** customizable messages/channels.
*   **role rewards:** automatically grant roles at specific level milestones.

### 4.6. counting
simple counting module, mathematics support, configurable
channel, roles, behaviour (multiple counts per user or 1 per user etc)

### 4.7. Tickets
*   **support system:** reaction or button-based ticket creation.
*   **transcription:** auto-save logs of ticket conversations upon closing.
*   **private channels:** dedicated temporary channels for user-staff interaction.

### 4.8. Logging
*   **event logs:** message edits/deletes, member joins/leaves, role changes, server changes (name, icon, etc.)
*   **categorization:** ability to route different log types to different channels.

---

## 5. User Interface (Frontend Dashboard)
*   **Technology:** html + css + js
*   **Visual Style:** 
    *   **Typography:** SignPainter for displays, Roboto for text.
    *   **Case:** strictly lowercase everywhere.
    *   **Colors:** primary (#98aa63), dark (#1a1e22).
    *   **Layout:** flat, no shadows, sharp corners, no gradients.
*   **Functionality:** real-time module toggles and configuration forms.

---

## 6. Technical Stack (Proposed)
*   **Language:** python bot > html + css + js dashboard (hosted under a hypercorn process, using sqlalchemy for database interactions) + discord oauth2 for user authentication
*   **Library:** discord.py
*   **Database:** Sqlalchemy (Core data) and Redis (Caching/Economy).

---

## 7. Roadmap
1.  **Phase 1:** Core framework and Module Management.
2.  **Phase 3:** Base commands and Logging.
3.  **Phase 3:** Moderation and Tickets.
4.  **Phase 4:** FrogBoard, Levels, and Economy.
5.  **Phase 5:** Games and Web Dashboard.

being able to easily expand upon melvin, and introduce new modules is a neccessity. use this sentance and keep it in mind when designing the base infastructure. Use and expand upon this prd to create a comprehensive and well-structured document that will guide the development of melvin.