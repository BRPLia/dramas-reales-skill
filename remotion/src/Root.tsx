import { Composition } from "remotion";
import { MainVideo } from "./Main";
import meta from "./meta.json";

// Una sola composicion. `Main.tsx` y `meta.json` los regenera el motor en cada
// render (python generar.py video <guion.json>). Aqui solo se registran.
export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Short"
      component={MainVideo}
      durationInFrames={meta.durationInFrames}
      fps={meta.fps}
      width={meta.width}
      height={meta.height}
    />
  );
};
