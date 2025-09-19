def search_reservas(self, id_reserva="", solicitante="", salon="", fecha=""):
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = "SELECT * FROM reservas WHERE 1=1"
        params = []

        if id_reserva:
            # Corrección: Intenta convertir el ID a un entero y maneja el error si no es un número.
            try:
                id_reserva_int = int(id_reserva)
                query += " AND id = ?"
                params.append(id_reserva_int)
            except ValueError:
                # Si el ID no es un número, la consulta no devolverá nada, lo que evita el error.
                return []

        if solicitante:
            query += " AND solicitante LIKE ?"
            params.append(f"%{solicitante}%")
        if salon:
            query += " AND salon = ?"
            params.append(salon)
        if fecha:
            query += " AND fecha = ?"
            params.append(fecha)

        query += " ORDER BY fecha_creacion DESC"
        cursor.execute(query, params)
        result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        print(f"Error al buscar reservas: {e}")
        return []
