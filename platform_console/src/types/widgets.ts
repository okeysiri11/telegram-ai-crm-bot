export interface WidgetDefinition {
  id: string;
  title: string;
  description?: string;
  defaultW: number;
  defaultH: number;
  minRole?: 'readonly' | 'administrator' | 'owner';
  channels?: string[];
}

export interface LayoutItem {
  id: string;
  widgetId: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface DashboardPreferences {
  layout: LayoutItem[];
  hiddenWidgets: string[];
}
