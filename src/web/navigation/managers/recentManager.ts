import { navigationHistory } from "./navigationHistory";
import { searchProvider } from "./searchProvider";

export const recentManager = {
  pages() {
    return navigationHistory.recentPages();
  },
  commands() {
    return navigationHistory.recentCommands();
  },
  searches() {
    return searchProvider.recent();
  },
  documents() {
    return navigationHistory.recentDocuments();
  },
};
