# Real-Time Collaboration Patterns

### When to add real-time

- Live coding exercises with instructor
- Collaborative document editing (group projects)
- Real-time Q&A during live sessions
- Peer review workflows
- Whiteboard/diagramming

### Technology Options

| Technology | Use case | Complexity | Scalability |
|------------|----------|-----------|-------------|
| WebSockets (ws/Socket.IO) | Chat, notifications, presence | Low | Medium (sticky sessions) |
| CRDT/Yjs | Collaborative text editing | Medium | High (conflict-free) |
| Yjs + y-websocket | Shared cursors, live editing | Medium | High |
| WebRTC | Video/audio, screen sharing | High | Peer-dependent |
| Server-Sent Events (SSE) | One-way updates, progress | Low | High |
| Liveblocks | Managed real-time (comments, presence) | Low (managed) | High |

### Architecture Patterns

1. **Presence + awareness** (simplest): WebSocket for online indicators, typing status.
   Stack: Socket.IO + Redis adapter for multi-node.
2. **Collaborative editing**: Yjs CRDT + y-websocket provider. No conflict resolution needed.
   Persistence: y-indexeddb (client) + y-leveldb or y-supabase (server).
3. **Live sessions**: WebRTC via mediasoup/LiveKit for video + WebSocket signaling.
   Fallback: TURN server for NAT traversal.
4. **Hybrid**: SSE for server-push (progress, notifications) + WebSocket for bidirectional
   (chat, collaboration). Avoid mixing unless needed.

### Scaling Considerations

- WebSocket: sticky sessions or Redis pub/sub for multi-node
- CRDT: stateless servers, state lives in document -- scales horizontally
- WebRTC: SFU (Selective Forwarding Unit) for >4 participants
- Always implement reconnection with exponential backoff
