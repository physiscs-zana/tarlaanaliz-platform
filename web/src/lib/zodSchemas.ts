// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.

export interface ParseResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface LoginDto {
  phone: string;
  pin: string;
}

export function parseLoginDto(input: unknown): ParseResult<LoginDto> {
  if (!input || typeof input !== 'object') return { success: false, error: 'Invalid payload' };
  const value = input as Record<string, unknown>;
  const phone = value.phone;
  const pin = value.pin;

  if (typeof phone !== 'string' || !/^\d{10,15}$/.test(phone)) return { success: false, error: 'Invalid phone' };
  if (typeof pin !== 'string' || !/^\d{6}$/.test(pin)) return { success: false, error: 'Invalid pin' };

  return { success: true, data: { phone, pin } };
}

export interface UploadDto {
  fileName: string;
  contentType: string;
  size: number;
}

export function parseUploadDto(input: unknown): ParseResult<UploadDto> {
  if (!input || typeof input !== 'object') return { success: false, error: 'Invalid payload' };
  const value = input as Record<string, unknown>;
  const fileName = value.fileName;
  const contentType = value.contentType;
  const size = value.size;

  if (typeof fileName !== 'string' || fileName.length === 0) return { success: false, error: 'Invalid fileName' };
  if (typeof contentType !== 'string' || contentType.length === 0) return { success: false, error: 'Invalid contentType' };
  if (typeof size !== 'number' || size <= 0) return { success: false, error: 'Invalid size' };

  return { success: true, data: { fileName, contentType, size } };
}
