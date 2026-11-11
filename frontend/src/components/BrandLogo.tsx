import React from 'react'

export const BrandLogo: React.FC<{ size?: number; showSubtitle?: boolean }> = ({
  size = 34,
  showSubtitle = false,
}) => {
  return (
    <div className="flex items-center gap-3 select-none">
      <svg
        width={size}
        height={size}
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="gayatriGrad" x1="4" y1="4" x2="36" y2="36" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#22D3EE" />
            <stop offset="55%" stopColor="#0EA5E9" />
            <stop offset="100%" stopColor="#10B981" />
          </linearGradient>
        </defs>
        <rect x="2" y="2" width="36" height="36" rx="10" fill="#0B1120" stroke="url(#gayatriGrad)" strokeWidth="1.75" />
        <polygon
          points="20,7 31,13.5 31,26.5 20,33 9,26.5 9,13.5"
          stroke="url(#gayatriGrad)"
          strokeWidth="1.6"
          fill="rgba(34, 211, 238, 0.08)"
        />
        <path
          d="M20 12.5L26.5 16.5V23.5L20 27.5L13.5 23.5V16.5L20 12.5Z"
          stroke="#34D399"
          strokeWidth="1.4"
        />
        <circle cx="20" cy="20" r="2.7" fill="#22D3EE" />
        <circle cx="20" cy="7.5" r="1.6" fill="#22D3EE" />
        <circle cx="30.5" cy="26" r="1.6" fill="#10B981" />
        <circle cx="9.5" cy="26" r="1.6" fill="#F59E0B" />
      </svg>
      <div className="leading-tight">
        <div className="text-base font-bold tracking-tight text-slate-100">
          Gayatri <span className="text-cyan-400">AI</span>
        </div>
        {showSubtitle && (
          <div className="text-[11px] font-medium tracking-wider uppercase text-slate-400">
            Educational Intelligence
          </div>
        )}
      </div>
    </div>
  )
}
