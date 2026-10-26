/** La Comadre Ajolota — the mascot.
 *
 *  Built to match the reference sticker: a side-on axolotl curled into a
 *  comma, head low-left, body sweeping right and the tail rising to the
 *  upper right behind a magenta fin. Six branched gills, four stubby toed
 *  limbs, belly lines, a long wavy mouth, two round eyes with catchlights.
 *
 *  The pose changes only the front limb and the eyes, so her silhouette
 *  never deforms — the previous version moved an arm across her face.
 */

export type Pose = "waving" | "reading" | "excited";

const INK = "#1F2A44";
const SKIN = "#F2ADA8";
const SKIN_DEEP = "#E89A96";
const GILL = "#EE7FA6";
const FIN = "#E8569A";
const BLUSH = "#F08098";
const BOOK = "#2487C1";
const BOOK_DARK = "#1A6894";

/** One feathered gill: a curved stem with fronds down both sides. */
function Gill({ x, y, rot, len }: { x: number; y: number; rot: number; len: number }) {
  const at = [0.3, 0.52, 0.72, 0.9];
  return (
    <g transform={`translate(${x} ${y}) rotate(${rot})`} stroke={INK} strokeWidth={5}>
      <path d={`M0 0 Q ${len * 0.55} -10 ${len} -14`} fill="none" stroke={GILL}
            strokeWidth={13} strokeLinecap="round" />
      {at.map((f, i) => {
        const px = len * f, py = -14 * f, s = 20 - i * 3;
        return (
          <g key={i} stroke={GILL} strokeWidth={9} strokeLinecap="round" fill="none">
            <path d={`M${px} ${py} L ${px + s * 0.35} ${py - s}`} />
            <path d={`M${px} ${py} L ${px + s * 0.4} ${py + s * 0.85}`} />
          </g>
        );
      })}
      <path d={`M0 0 Q ${len * 0.55} -10 ${len} -14`} fill="none" stroke={INK}
            strokeWidth={4.5} strokeLinecap="round" opacity={0.0} />
    </g>
  );
}

export function Ajolota({
  size = 120,
  pose = "waving",
  className = "",
}: { size?: number; pose?: Pose; className?: string }) {
  return (
    <svg
      className={`ajolota ajolota--${pose} ${className}`}
      width={size}
      height={size}
      viewBox="0 0 400 380"
      role="img"
      aria-label="La Comadre Ajolota"
      fill="none"
      stroke={INK}
      strokeWidth={7}
      strokeLinejoin="round"
      strokeLinecap="round"
    >
      <g className="aj-float">
        {/* ---------- gills, behind everything ---------- */}
        <g className="aj-gills">
          <Gill x={96} y={96} rot={-146} len={66} />
          <Gill x={78} y={128} rot={-178} len={62} />
          <Gill x={86} y={162} rot={158} len={54} />
          <Gill x={214} y={92} rot={-44} len={66} />
          <Gill x={236} y={118} rot={-16} len={62} />
          <Gill x={238} y={150} rot={12} len={54} />
        </g>

        {/* ---------- the tail fin, a magenta ribbon on the outer edge ---------- */}
        <g className="aj-tail">
          <path
            d="M298 118
               C 344 138, 368 194, 356 250
               C 344 298, 302 324, 256 314
               C 294 300, 326 270, 336 230
               C 346 188, 332 144, 298 126 Z"
            fill={FIN}
          />
          {/* ---------- body and tail ---------- */}
          <path
            d="M196 190
               C 244 186, 286 206, 304 244
               C 318 274, 310 306, 282 318
               C 252 330, 220 316, 206 290
               C 226 302, 250 300, 262 286
               C 276 268, 268 244, 244 232
               C 226 222, 206 218, 190 220 Z"
            fill={SKIN}
          />
          <path d="M268 250 C 282 262, 286 282, 278 296" stroke={SKIN_DEEP} strokeWidth={5} />
        </g>

        {/* ---------- hind limb ---------- */}
        <path d="M206 250 C 214 276, 206 294, 186 292 C 174 290, 170 280, 174 270"
              fill={SKIN_DEEP} />
        <path d="M176 290 L 170 300 M186 294 L 184 306 M196 290 L 200 302"
              strokeWidth={5} />

        {/* ---------- head and front body ---------- */}
        <path
          d="M158 44
             C 220 44, 254 86, 254 136
             C 254 190, 214 226, 158 226
             C 100 226, 62 190, 62 136
             C 62 86, 98 44, 158 44 Z"
          fill={SKIN}
        />

        {/* belly segments, the little lines on the reference */}
        <path d="M108 200 C 128 216, 170 218, 196 204" stroke={SKIN_DEEP} strokeWidth={5} />
        <path d="M126 212 L 124 224 M152 218 L 152 230 M178 214 L 182 226"
              stroke={SKIN_DEEP} strokeWidth={4.5} />

        {/* ---------- front limb ---------- */}
        {pose === "reading" ? (
          <>
            <path d="M96 212 C 80 232, 84 252, 106 252" fill={SKIN_DEEP} />
            <g className="aj-book">
              <path d="M82 240 L 162 228 L 162 296 L 82 308 Z" fill={BOOK} />
              <path d="M242 240 L 162 228 L 162 296 L 242 308 Z" fill={BOOK_DARK} />
              <path d="M162 228 L 162 296" />
            </g>
          </>
        ) : pose === "excited" ? (
          <g className="aj-arm-l">
            <path d="M92 196 C 62 182, 44 150, 52 120" fill={SKIN_DEEP} />
            <path d="M42 116 L 52 120 L 46 108" strokeWidth={5} />
          </g>
        ) : (
          <g className="aj-wave">
            {/* kept to the left of the head so it never crosses her face */}
            <path d="M94 200 C 66 188, 46 158, 50 124" fill={SKIN_DEEP} />
            <ellipse cx="50" cy="114" rx="20" ry="17" fill={SKIN_DEEP}
                     transform="rotate(14 50 114)" />
            <path d="M38 98 L 32 86 M50 94 L 50 80 M62 98 L 68 86" strokeWidth={5} />
          </g>
        )}

        {/* ---------- face ---------- */}
        {pose === "waving" ? (
          <>
            <ellipse cx="136" cy="128" rx="13" ry="15" fill={INK} stroke="none" />
            <ellipse cx="196" cy="126" rx="13" ry="15" fill={INK} stroke="none" />
            <circle cx="140" cy="121" r="4.4" fill="#fff" stroke="none" />
            <circle cx="200" cy="119" r="4.4" fill="#fff" stroke="none" />
          </>
        ) : (
          <>
            <path d="M122 128 C 130 115, 146 115, 154 128" strokeWidth={7} />
            <path d="M182 126 C 190 113, 206 113, 214 126" strokeWidth={7} />
          </>
        )}

        <ellipse cx="96" cy="162" rx="19" ry="11" fill={BLUSH} opacity="0.4" stroke="none" />
        <ellipse cx="222" cy="158" rx="16" ry="10" fill={BLUSH} opacity="0.3" stroke="none" />

        {/* the long wavy axolotl mouth */}
        {pose === "excited" ? (
          <path d="M138 166 C 148 190, 180 190, 190 166 C 178 178, 150 178, 138 166 Z"
                fill={INK} stroke="none" />
        ) : (
          <path d="M128 160 C 140 176, 154 176, 164 162 C 174 176, 188 176, 198 160"
                strokeWidth={6} />
        )}
      </g>
    </svg>
  );
}

/** Her working state: reading, with the dots beside her. */
export function AjolotaThinking({ label }: { label: string }) {
  return (
    <div className="ajolota-thinking">
      <Ajolota size={70} pose="reading" />
      <span className="dots" aria-label={label}><span /><span /><span /></span>
    </div>
  );
}
