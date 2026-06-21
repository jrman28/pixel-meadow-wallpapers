import {ThreeCanvas} from "@remotion/three";
import {useLoader} from "@react-three/fiber";
import {useMemo} from "react";
import {
  ClampToEdgeWrapping,
  NearestFilter,
  NoToneMapping,
  ShaderMaterial,
  SRGBColorSpace,
  TextureLoader,
} from "three";
import {AbsoluteFill, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {CLOUDS, PLATE_HEIGHT, PLATE_WIDTH} from "./clouds";
import {LOOP_FRAMES, moonGlow, starTwinkle} from "./motion";

export type PixelMeadowWallpaperProps = {readonly variant: "day" | "night"};

const roundGlsl = (value: number) => value.toFixed(8);

const cloudWarpShader = CLOUDS.map((cloud, index) => {
  const centerX = (cloud.x + cloud.width / 2) / PLATE_WIDTH;
  const centerY = 1 - (cloud.y + cloud.height / 2) / PLATE_HEIGHT;
  const radiusX = (cloud.width * 0.72) / PLATE_WIDTH;
  const radiusY = (cloud.height * 0.82) / PLATE_HEIGHT;
  const amplitudeX = 6 + cloud.depth * 12;
  const amplitudeY = 0.75 + cloud.depth * 1.25;
  const phase = index * 0.73;
  const verticalPhase = index * 0.41;

  return `
    vec2 cloudDelta${index}=(vUv-vec2(${roundGlsl(centerX)},${roundGlsl(centerY)}))/vec2(${roundGlsl(radiusX)},${roundGlsl(radiusY)});
    float cloudInfluence${index}=1.0-smoothstep(0.72,1.0,length(cloudDelta${index}));
    float cloudPhase${index}=TAU*uProgress+${roundGlsl(phase)};
    float cloudX${index}=roundPixel(sin(cloudPhase${index})*${roundGlsl(amplitudeX)});
    float cloudY${index}=roundPixel(sin(cloudPhase${index}*2.0+${roundGlsl(verticalPhase)})*${roundGlsl(amplitudeY)});
    sampleUv+=vec2(-cloudX${index}/uOutputWidth,cloudY${index}/uOutputHeight)*cloudInfluence${index};`;
}).join("\n");

const vertexShader = `
  varying vec2 vUv;
  void main() {
    vUv=uv;
    gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);
  }
`;

const fragmentShader = `
  uniform sampler2D uTexture;
  uniform float uProgress;
  uniform float uOutputWidth;
  uniform float uOutputHeight;
  varying vec2 vUv;
  const float TAU=6.28318530718;

  float roundPixel(float value) {
    return sign(value)*floor(abs(value)+0.5);
  }

  void main() {
    vec2 sampleUv=vUv;

    float grassInfluence=smoothstep(0.02,0.13,vUv.y)*(1.0-smoothstep(0.30,0.40,vUv.y));
    float waveSix=sin(TAU*4.0*uProgress+vUv.x*11.5);
    float waveTwelve=sin(TAU*2.0*uProgress+vUv.x*5.25+0.8);
    float grassPixels=roundPixel(8.0*grassInfluence*(waveSix*0.68+waveTwelve*0.32));
    sampleUv.x-=grassPixels/uOutputWidth;

    ${cloudWarpShader}

    sampleUv=clamp(sampleUv,vec2(0.0),vec2(1.0));
    gl_FragColor=texture2D(uTexture,sampleUv);
  }
`;

const PixelPlate = ({variant}: PixelMeadowWallpaperProps) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const texture = useLoader(
    TextureLoader,
    staticFile(`wallpapers/${variant}/plate.png`),
  );
  const material = useMemo(() => {
    texture.colorSpace = SRGBColorSpace;
    texture.magFilter = NearestFilter;
    texture.minFilter = NearestFilter;
    texture.generateMipmaps = false;
    texture.wrapS = ClampToEdgeWrapping;
    texture.wrapT = ClampToEdgeWrapping;
    texture.needsUpdate = true;

    return new ShaderMaterial({
      fragmentShader,
      vertexShader,
      toneMapped: false,
      uniforms: {
        uTexture: {value: texture},
        uProgress: {value: 0},
        uOutputWidth: {value: width},
        uOutputHeight: {value: height},
      },
    });
  }, [height, texture, width]);

  material.uniforms.uProgress.value = (frame % LOOP_FRAMES) / LOOP_FRAMES;

  return (
    <ThreeCanvas
      width={width}
      height={height}
      orthographic
      camera={{position: [0, 0, 10], zoom: 1}}
      dpr={1}
      gl={{antialias: false, preserveDrawingBuffer: true, toneMapping: NoToneMapping}}
    >
      <ambientLight intensity={1} />
      <mesh material={material}>
        <planeGeometry args={[width, height]} />
      </mesh>
    </ThreeCanvas>
  );
};

const StarGlints = () => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const scaleX = width / PLATE_WIDTH;
  const scaleY = height / PLATE_HEIGHT;
  const stars = [
    [84, 128], [285, 122], [498, 145], [620, 253], [847, 132],
    [930, 122], [1062, 174], [1504, 144], [1584, 152], [84, 408],
  ] as const;

  return stars.map(([x, y], index) => (
    <div
      key={`${x}-${y}`}
      style={{
        position: "absolute",
        left: x * scaleX - 2,
        top: y * scaleY - 2,
        width: 4,
        height: 4,
        backgroundColor: "#fffbd7",
        boxShadow: "0 0 7px 2px rgba(183,220,255,0.55)",
        opacity: (starTwinkle(frame, index) - 0.72) * 0.7,
      }}
    />
  ));
};

export const PixelMeadowWallpaper = ({variant}: PixelMeadowWallpaperProps) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const scaleX = width / PLATE_WIDTH;
  const scaleY = height / PLATE_HEIGHT;

  return (
    <AbsoluteFill style={{backgroundColor: variant === "day" ? "#139df0" : "#020923"}}>
      <PixelPlate variant={variant} />
      {variant === "night" ? (
        <div
          style={{
            position: "absolute",
            left: 1150 * scaleX,
            top: 145 * scaleY,
            width: 285 * scaleX,
            height: 285 * scaleY,
            borderRadius: "50%",
            background: "radial-gradient(circle,rgba(210,232,255,.18) 0%,rgba(92,157,235,.08) 42%,transparent 72%)",
            opacity: moonGlow(frame),
            pointerEvents: "none",
          }}
        />
      ) : null}
      {variant === "night" ? <StarGlints /> : null}
    </AbsoluteFill>
  );
};
