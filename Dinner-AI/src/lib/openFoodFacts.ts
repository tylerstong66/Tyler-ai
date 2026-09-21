export type BarcodeProduct = {
  barcode: string;
  name: string;
  brand?: string;
  imageUrl?: string;
};

export async function lookupBarcode(barcode: string): Promise<BarcodeProduct | null> {
  const fields = 'code,product_name,brands,image_front_url';
  const url = `https://world.openfoodfacts.org/api/v3/product/${encodeURIComponent(barcode)}.json?fields=${fields}`;

  const response = await fetch(url, {
    headers: {
      'User-Agent': 'DinnerAI/0.1 (prototype barcode scan)'
    }
  });

  if (!response.ok) {
    if (response.status === 404) return null;
    throw new Error(`Product lookup failed (${response.status})`);
  }

  const data = await response.json();
  const product = data?.product;
  if (!product) return null;

  const name = product.product_name?.trim();
  if (!name) return null;

  return {
    barcode,
    name,
    brand: product.brands?.trim() || undefined,
    imageUrl: product.image_front_url || undefined
  };
}
