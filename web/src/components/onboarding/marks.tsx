import type { ReactElement } from "react";

const I = "currentColor";

const wrap = (children: ReactElement): ReactElement => (
  <svg width={22} height={22} viewBox="0 0 24 24" fill="none" style={{ display: "block" }}>
    {children}
  </svg>
);

export type MarkKey =
  | "github"
  | "openai"
  | "anthropic"
  | "postgres"
  | "stripe"
  | "slack"
  | "linear"
  | "supabase"
  | "vercel"
  | "notion"
  | "aws"
  | "sentry";

export const Marks: Record<MarkKey, ReactElement> = {
  github: wrap(
    <>
      <circle cx="12" cy="12" r="9" fill={I} />
      <path
        d="M12 6.5c-2.7 0-5 2.2-5 4.9 0 2.2 1.4 4 3.4 4.7.2 0 .3-.1.3-.2v-.9c-1.4.3-1.7-.6-1.7-.6-.2-.6-.5-.7-.5-.7-.5-.3.04-.3.04-.3.5 0 .8.5.8.5.5.8 1.2.6 1.5.4 0-.4.2-.6.4-.8-1.1-.1-2.3-.5-2.3-2.4 0-.5.2-1 .5-1.3-.05-.1-.2-.6.05-1.3 0 0 .4-.1 1.4.5.4-.1.8-.2 1.3-.2.4 0 .9.05 1.3.2 1-.7 1.4-.5 1.4-.5.3.7.1 1.2.05 1.3.3.3.5.8.5 1.3 0 1.9-1.2 2.3-2.3 2.4.2.2.4.5.4 1v1.5c0 .1.1.2.3.2C15.6 15.4 17 13.6 17 11.4c0-2.7-2.3-4.9-5-4.9z"
        fill="#fff"
      />
    </>,
  ),
  openai: wrap(
    <>
      <circle cx="12" cy="12" r="8" stroke={I} strokeWidth="1.5" fill="none" />
      <path d="M12 6 L17 9 L17 15 L12 18 L7 15 L7 9 z" stroke={I} strokeWidth="1.2" fill="none" />
    </>,
  ),
  anthropic: wrap(
    <path
      d="M9 5 L5 19 H8 L9 16 H13 L14 19 H17 L13 5 z M10 13 L11 9 L12 13 z"
      fill={I}
    />,
  ),
  postgres: wrap(
    <>
      <ellipse cx="12" cy="8" rx="7" ry="2.5" fill={I} />
      <path
        d="M5 8 V16 C5 17.5 8 18.5 12 18.5 C16 18.5 19 17.5 19 16 V8"
        stroke={I}
        strokeWidth="1.5"
        fill="none"
      />
      <ellipse cx="12" cy="12" rx="7" ry="2.5" fill="none" stroke={I} strokeWidth="1.5" />
    </>,
  ),
  stripe: wrap(
    <path
      d="M16 7 H8 C6 7 6 10 8 10 L14 12 C16 12.5 16 16 14 16 H7"
      stroke={I}
      strokeWidth="2"
      fill="none"
    />,
  ),
  slack: wrap(
    <>
      <rect x="4" y="10" width="6" height="2" rx="1" fill={I} />
      <rect x="14" y="12" width="6" height="2" rx="1" fill={I} />
      <rect x="10" y="4" width="2" height="6" rx="1" fill={I} />
      <rect x="12" y="14" width="2" height="6" rx="1" fill={I} />
    </>,
  ),
  linear: wrap(
    <>
      <circle cx="12" cy="12" r="8" stroke={I} strokeWidth="1.5" fill="none" />
      <path
        d="M6 12 L18 12 M6 8 L18 8 M6 16 L18 16"
        stroke={I}
        strokeWidth="1.5"
      />
    </>,
  ),
  supabase: wrap(
    <path d="M12 4 L4 14 H10 L8 20 L20 10 H14 L16 4 z" fill={I} />,
  ),
  vercel: wrap(<path d="M12 5 L21 19 H3 z" fill={I} />),
  notion: wrap(
    <>
      <rect x="5" y="4" width="14" height="16" rx="1" fill={I} />
      <path
        d="M9 8 L9 16 M9 8 L15 14 L15 8"
        stroke="#fff"
        strokeWidth="1.5"
        fill="none"
      />
    </>,
  ),
  aws: wrap(
    <>
      <path
        d="M4 14 C7 17 17 17 20 14"
        stroke={I}
        strokeWidth="1.8"
        fill="none"
      />
      <path
        d="M5 9 H8 V12 H5z M10 9 H13 V12 H10z M15 9 H18 V12 H15z"
        fill={I}
      />
    </>,
  ),
  sentry: wrap(
    <path
      d="M12 4 L20 18 H15 A3 3 0 0 0 9 18 L12 12 L15 17 L17 17 L12 7 L7 17 H4 z"
      fill={I}
    />,
  ),
};
