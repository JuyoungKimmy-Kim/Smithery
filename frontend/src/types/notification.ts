export interface Notification {
  id: number;
  type: 'comment' | 'favorite' | 'status_change' | 'new_mcp';
  message: string;
  is_read: boolean;
  created_at: string;
  mcp_server_id: number | null;
  related_user_id: number | null;
}

export interface UnreadCountResponse {
  count: number;
}

export interface MarkReadResponse {
  success: boolean;
  message: string;
}
