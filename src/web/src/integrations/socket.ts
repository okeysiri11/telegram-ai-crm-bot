import { io, type Socket } from "socket.io-client";
import { webConfig } from "@/config/webConfig";

let socket: Socket | null = null;

export function getSocket(): Socket | null {
  if (!webConfig.socketUrl) return null;
  if (!socket) {
    socket = io(webConfig.socketUrl, { autoConnect: false });
  }
  return socket;
}
