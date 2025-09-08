import os
from PIL import Image

def convert_png_to_jpeg(input_dir, output_dir):
    """
    Converte tutte le immagini PNG in JPEG ricreando la stessa struttura di cartelle.
    """
    for root, dirs, files in os.walk(input_dir):
        # Calcola il percorso relativo dalla cartella input
        rel_path = os.path.relpath(root, input_dir)
        # Crea la cartella corrispondente in output
        out_path = os.path.join(output_dir, rel_path)
        os.makedirs(out_path, exist_ok=True)

        for file in files:
            if file.lower().endswith(".png"):
                input_path = os.path.join(root, file)
                output_file = os.path.splitext(file)[0] + ".jpeg"
                output_path = os.path.join(out_path, output_file)

                try:
                    with Image.open(input_path) as img:
                        rgb_img = img.convert("RGB")  # JPEG non supporta trasparenza
                        rgb_img.save(output_path, "JPEG", quality=95)
                    print(f"✅ Convertito: {input_path} -> {output_path}")
                except Exception as e:
                    print(f"❌ Errore con {input_path}: {e}")

if __name__ == "__main__":
    convert_png_to_jpeg("input_png", "output_jpeg")
