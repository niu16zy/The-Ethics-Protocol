import { LevelOnePage } from "./pages/LevelOnePage";
import { levels } from "./config/levels";

function activeLevelId(): number {
  const params = new URLSearchParams(window.location.search);
  const queryLevel = Number(params.get("level"));
  if (Number.isInteger(queryLevel) && queryLevel > 0) {
    return queryLevel;
  }

  const pathMatch = window.location.pathname.match(/level-?(\d+)/i);
  if (pathMatch) {
    return Number(pathMatch[1]);
  }

  return 1;
}

export default function App() {
  const level = levels.find((candidate) => candidate.levelId === activeLevelId()) ?? levels[0];

  return <LevelOnePage level={level} />;
}
