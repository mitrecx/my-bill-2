export const formatBarTopInteger = (value: number | null | undefined): string => {
  if (value == null || value === 0) return '';
  return Math.round(value).toLocaleString('zh-CN');
};

export const barTopIntegerLabel = {
  show: true,
  position: 'outside' as const,
  distance: 4,
  formatter: (params: { value?: number | null }) => formatBarTopInteger(params.value),
};

export const signedBarTopIntegerLabel = {
  show: true,
  position: 'outside' as const,
  distance: 4,
  formatter: (params: { value?: number | null }) => formatBarTopInteger(params.value),
};
