// src/components/Icons.tsx
import React from "react";

/**
 * 统一封装 SVG 容器
 * 所有 icon 视觉风格都会从这里统一控制（黑白线条、使用 currentColor）
 */
type IconProps = {
  size?: number;
  className?: string;
};

const IconWrapper = ({
  children,
  size = 20,
  className,
}: {
  children: React.ReactNode;
  size?: number;
  className?: string;
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    {children}
  </svg>
);

/* ======================
   Login 会用到的 Eye / EyeOff（✅ 必须保留这些 export 名称）
====================== */

export const EyeIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
    <circle cx="12" cy="12" r="3" />
  </IconWrapper>
);

export const EyeOffIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
    <line x1="1" y1="1" x2="23" y2="23" />
  </IconWrapper>
);

/* ======================
   Sidebar / Header icons
====================== */

export const MenuIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <line x1="3" y1="6" x2="21" y2="6" />
    <line x1="3" y1="12" x2="21" y2="12" />
    <line x1="3" y1="18" x2="21" y2="18" />
  </IconWrapper>
);

export const SearchIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <circle cx="11" cy="11" r="8" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
  </IconWrapper>
);

export const PenIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="M12 20h9" />
    <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4 11.5-11.5z" />
  </IconWrapper>
);

/* 你原本的 GuitarIcon（如果其他地方还有用到，保留避免再炸） */
export const GuitarIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    <path d="M14.5 5.5a3.5 3.5 0 0 1 5 5L14 16a4 4 0 1 1-6-6l6.5-4.5z" />
    <path d="M13 7l4 4" />
  </IconWrapper>
);

/* ✅ 抽象吉他 icon（给你右上角红框用） */
export const AbstractGuitarIcon = (props: IconProps) => (
  <IconWrapper {...props}>
    {/* 颈部 */}
    <path d="M14 4l6 6" />
    {/* 琴头（点） */}
    <circle cx="19.2" cy="4.8" r="0.7" />
    <circle cx="20.6" cy="6.2" r="0.7" />
    {/* 琴身（抽象曲线） */}
    <path d="M13.2 9.2c-1.4-1.4-3.8-1.4-5.2 0-1.4 1.4-1.4 3.8 0 5.2 1.4 1.4 3.8 1.4 5.2 0" />
    <path d="M13.2 9.2c1.2 1.2 1.2 3.2 0 4.4-1.2 1.2-3.2 1.2-4.4 0" />
    {/* 连接 */}
    <path d="M12.8 8.8l1.8-1.8" />
  </IconWrapper>
);



