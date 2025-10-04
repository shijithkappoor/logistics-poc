import React, { useRef, useState, useEffect } from 'react';

interface ResizableProps {
	minHeight?: number;
	maxHeight?: number;
	initialHeight?: number | string;
	children: React.ReactNode;
	style?: React.CSSProperties;
}

export default function Resizable({ minHeight = 100, maxHeight = 800, initialHeight = 240, children, style }: ResizableProps) {
	const ref = useRef<HTMLDivElement | null>(null);
	const [height, setHeight] = useState<number | string>(initialHeight);
	const draggingRef = useRef(false);
	const startYRef = useRef(0);
	const startHRef = useRef<number | null>(null);

	useEffect(() => {
		function onMove(e: MouseEvent) {
			if (!draggingRef.current) return;
			const dy = startYRef.current - e.clientY; // dragging the top edge
			const startH = startHRef.current ?? (ref.current ? ref.current.offsetHeight : 0);
			const newH = Math.min(maxHeight, Math.max(minHeight, startH + dy));
			setHeight(newH);
		}

		function onUp() {
			draggingRef.current = false;
			startHRef.current = null;
		}

		window.addEventListener('mousemove', onMove);
		window.addEventListener('mouseup', onUp);
		return () => {
			window.removeEventListener('mousemove', onMove);
			window.removeEventListener('mouseup', onUp);
		};
	}, [minHeight, maxHeight]);

	function onMouseDown(e: React.MouseEvent) {
		draggingRef.current = true;
		startYRef.current = e.clientY;
		startHRef.current = ref.current ? ref.current.offsetHeight : null;
		e.preventDefault();
	}

	return (
		<div ref={ref} style={{ height: typeof height === 'number' ? `${height}px` : height, position: 'relative', ...style }}>
			{/* Top drag handle */}
			<div
				onMouseDown={onMouseDown}
				style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 8, cursor: 'ns-resize', zIndex: 20 }}
				aria-hidden
			/>
			<div style={{ height: '100%', overflow: 'auto' }}>{children}</div>
		</div>
	);
}
