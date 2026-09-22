export type BarcodeProduct = {
  barcode: string;
  name: string;
  brand?: string;
  imageUrl?: string;
};

const LOOKUP_TIMEOUT_MS = 12_000;

export async function lookupBarcode(barcode: string): Promise<BarcodeProduct | null> {
  const cleanBarcode = barcode.trim();
  if (!/^[0-9]{6,14}$/.test(cleanBarcode)) throw new Error('That barcode format is not supported.');

  const fields = 'code,product_name,brands,image_front_url';
  const url = `https://world.openfoodfacts.org/api/v3/product/${encodeURIComponent(cleanBarcode)}.json?fields=${fields}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), LOOKUP_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
        'User-Agent': 'DinnerAI/0.9-beta'
      },
      signal: controller.signal
    });

    if (!response.ok) {
      if (response.status === 404) return null;
      throw new Error('The food database is unavailable right now. Please try again.');
    }

    const data = await response.json();
    const product = data?.product;
    if (!product) return null;

    const name = typeof product.product_name === 'string' ? product.product_name.trim() : '';
    if (!name) return null;

    return {
      barcode: cleanBarcode,
      name,
      brand: typeof product.brands === 'string' ? product.brands.trim() || undefined : undefined,
      imageUrl: typeof product.image_front_url === 'string' ? product.image_front_url : undefined
    };
  } catch (error: any) {
    if (error?.name === 'AbortError') throw new Error('The barcode lookup timed out. Please try again.');
    throw error;
  } finally {
    clearTimeout(timer);
  }
}
