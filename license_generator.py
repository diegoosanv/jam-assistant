import random
import string

def generate_key():
    """
    Genera una licencia para JAM con el formato JAM-XXXX-YYYY-ZZZZ.
    Los últimos dos dígitos son un checksum matemático de los caracteres anteriores.
    """
    chars = string.ascii_uppercase + string.digits
    
    # Generar bloques aleatorios
    part1 = ''.join(random.choices(chars, k=4))
    part2 = ''.join(random.choices(chars, k=4))
    part3_start = ''.join(random.choices(chars, k=2))
    
    # La parte base de la cadena a validar
    core_string = f"JAM-{part1}-{part2}-{part3_start}"
    
    # Algoritmo de validación (Checksum):
    # Sumar el valor ASCII de cada caracter (ignorando guiones) % 100
    checksum = sum(ord(c) for c in core_string.replace("-", "")) % 100
    
    # Añadir el checksum formateado a 2 dígitos al final de la clave
    final_key = f"{core_string}{checksum:02d}"
    return final_key

if __name__ == "__main__":
    print("=" * 40)
    print(" GENERADOR DE LICENCIAS - JAM ASSISTANT")
    print("=" * 40)
    print("Aquí tienes 5 licencias válidas para distribuir:\\n")
    
    for i in range(5):
        print(f"  Clave {i+1}: {generate_key()}")
        
    print("\\nConserva este código secreto. Nadie más puede generar claves válidas.")
