import "./index.css";
import {Composition, Folder} from "remotion";
import {PixelMeadowWallpaper} from "./PixelMeadowWallpaper";
import {FPS, LOOP_FRAMES} from "./motion";

const WIDTH = 2560;
const HEIGHT = 1600;

export const RemotionRoot: React.FC = () => (
  <Folder name="Pixel-Meadow-Wallpapers">
    <Composition id="PixelMeadow-Day" component={PixelMeadowWallpaper} durationInFrames={LOOP_FRAMES}
      fps={FPS} width={WIDTH} height={HEIGHT} defaultProps={{variant: "day" as const}} />
    <Composition id="PixelMeadow-Night" component={PixelMeadowWallpaper} durationInFrames={LOOP_FRAMES}
      fps={FPS} width={WIDTH} height={HEIGHT} defaultProps={{variant: "night" as const}} />
  </Folder>
);
