const SocialModel = {
    users: [],
    conversations: [],
    messages: [],
    presence: {},

    createUser(user) {
        const profile = {
            id: user.id,
            name: user.name,
            country: user.country || "",
            language: user.language || "fr",
            role: user.role || "user",
            avatar: user.avatar || "",
            bio: user.bio || "",
            createdAt: new Date().toISOString()
        };

        this.users.push(profile);
        return profile;
    },

    setPresence(userId, status) {
        this.presence[userId] = {
            status,
            lastSeen: new Date().toISOString()
        };
    },

    getPresence(userId) {
        return this.presence[userId] || {
            status: "offline",
            lastSeen: null
        };
    },

    createConversation(userA, userB) {
        const conversation = {
            id: crypto.randomUUID(),
            participants: [userA, userB],
            createdAt: new Date().toISOString()
        };

        this.conversations.push(conversation);
        return conversation;
    },

    sendMessage(conversationId, senderId, text) {
        if (!text || !text.trim()) {
            throw new Error("Message vide");
        }

        const message = {
            id: crypto.randomUUID(),
            conversationId,
            senderId,
            text: text.trim(),
            createdAt: new Date().toISOString()
        };

        this.messages.push(message);
        return message;
    },

    getMessages(conversationId) {
        return this.messages.filter(
            message => message.conversationId === conversationId
        );
    }
};

window.SocialModel = SocialModel;
