const SocialModel = {

    API: window.AGRINOVA_API.social,

    async request(path, options = {}) {

        const response = await fetch(
            this.API + path,
            {
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                    ...(options.headers || {})
                },
                ...options
            }
        );

        let data = {};

        try {
            data = await response.json();
        } catch (_) {}

        if (!response.ok) {
            throw new Error(
                data.error || "Erreur Social API"
            );
        }

        return data;
    },


    async getUsers() {

        const data = await this.request(
            "/api/users"
        );

        return data.users || [];
    },


    async createUser(user) {

        const data = await this.request(
            "/api/users",
            {
                method: "POST",
                body: JSON.stringify({
                    name: user.name,
                    country: user.country || "",
                    language: user.language || "fr",
                    role: user.role || "user",
                    avatar: user.avatar || "",
                    bio: user.bio || ""
                })
            }
        );

        return data.user;
    },


    async setPresence(userId, status) {

        return this.request(
            "/api/presence",
            {
                method: "POST",
                body: JSON.stringify({
                    user_id: userId,
                    status
                })
            }
        );
    },


    async createConversation(userA, userB) {

        const data = await this.request(
            "/api/conversations",
            {
                method: "POST",
                body: JSON.stringify({
                    user_a: userA,
                    user_b: userB
                })
            }
        );

        return data.conversation;
    },


    async getMessages(conversationId) {

        const data = await this.request(
            "/api/conversations/" +
            encodeURIComponent(conversationId)
        );

        return data.messages || [];
    },


    async sendMessage(
        conversationId,
        senderId,
        text
    ) {

        if (!text || !text.trim()) {
            throw new Error("Message vide");
        }

        const data = await this.request(
            "/api/messages",
            {
                method: "POST",
                body: JSON.stringify({
                    conversation_id: conversationId,
                    sender_id: senderId,
                    body: text.trim()
                })
            }
        );

        return data.message;
    }

};

window.SocialModel = SocialModel;
