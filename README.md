# CipherText Enterprise P2P
> **Secure, Zero-Trace, Anonymous Chat Communication.**

CipherText is an enterprise-grade secure messaging application built with React Native (Expo) and Firebase. It features the **A.E.G.I.S Protocol** (Automated Encryption & Guard Information System), ensuring that messages are truly ephemeral and vaporized from the server milliseconds after being read.

## 🚀 Features

- **A.E.G.I.S Zero-Trace Protocol:** Messages are stored in ephemeral queues. Once downloaded to the recipient's RAM, the server footprint is permanently deleted.
- **Panic Mode (☢️):** Instantly wipe all local memory, presence state, and SecureStore data with a single button press.
- **Enterprise UI:** Designed for professional environments with a terminal-inspired, monolithic monospace aesthetic.
- **Real-Time Push Notifications:** Native Android/iOS push integrations for alerts without compromising content security.
- **Admin Control Panel:** A standalone Python script for license management, remote account wiping, and global announcements.

## 🏗 Architecture

### 1. The Ephemeral Queue
Instead of storing chat histories in a centralized database, CipherText relies on transient pathways:
1. Sender encrypts and sends a payload to `ephemeral_messages/<target_id>/<msg_id>`.
2. Target's device listens for new child nodes.
3. Upon receiving the payload, Target's device issues an immediate `remove()` command to the server and stores the message in volatile RAM.
4. When the chat screen unmounts, the RAM is garbage-collected. No local SQLite databases or AsyncStorages are used for messages.

### 2. Presence & Signaling
Using Firebase `onDisconnect`, the app handles offline states gracefully. The `chat_signals` pathway is used for real-time connection teardowns. If a user triggers the Panic Button or exits the chat, a `CLOSE` signal is broadcasted and the tunnel is collapsed.

## 🛠 Tech Stack

- **Frontend:** React Native, Expo, React Navigation, Reanimated.
- **Backend/State:** Firebase Realtime Database.
- **Admin Panel:** Python 3 (CLI).
- **Security:** AES-256 (via crypto-js) and Expo SecureStore.

## 📜 Setup Instructions

1. Clone the repository.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Add your Firebase credentials to `src/core/firebaseConfig.js`.
4. Run the development server:
   ```bash
   npx expo start
   ```

*Note: For Android Release builds (APK), ensure you compile with EAS to bundle the native Reanimated modules properly.*

---
**Developed by:** DougoBrasil
