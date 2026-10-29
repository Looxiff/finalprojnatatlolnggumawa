from datetime import datetime, timedelta

class SeatManager:
    def __init__(self):
        self._owners = {}
        self._reservations = {}

    def status(self, seat_id):
        if seat_id in self._owners:
            return "occupied"
        if seat_id in self._reservations and len(self._reservations[seat_id]) > 0:
            return "reserved"
        return "available"

    def owner(self, seat_id):
        return self._owners.get(seat_id)

    def get_date_reservation_count(self, date_str):
        total = 0
        for res_list in self._reservations.values():
            for res in res_list:
                if res["date"] == date_str:
                    total += 1
        return total

    def is_date_overbooked(self, date_str):
        return self.get_date_reservation_count(date_str) >= 5

    def check_time_overlap(self, seat_id, date_str, new_start, new_end):
        if seat_id not in self._reservations:
            return False
        for res in self._reservations[seat_id]:
            if res["date"] == date_str:
                if max(res["start"], new_start) < min(res["end"], new_end):
                    return True
        return False

    def reserve(self, seat_id, student_number, date_str, start_dt, duration_hours):
        end_dt = start_dt + timedelta(hours=duration_hours)

        if self.is_date_overbooked(date_str):
            return False, "This date is fully booked (Maximum 5 reservations allowed per day)."

        if self.check_time_overlap(seat_id, date_str, start_dt, end_dt):
            return False, "The selected time slot overlaps with an existing reservation for this seat."

        if seat_id not in self._reservations:
            self._reservations[seat_id] = []

        self._reservations[seat_id].append({
            "student": student_number,
            "date": date_str,
            "start": start_dt,
            "end": end_dt
        })
        return True, f"Seat {seat_id} successfully reserved for {date_str}!"

    def occupy(self, seat_id, student_number):
        if seat_id in self._owners:
            return False, "This seat is already occupied."
        self._owners[seat_id] = student_number
        return True, f"Seat {seat_id} occupied."

    def release(self, seat_id, student_number):
        cleared = False

        if seat_id in self._owners:
            if self._owners[seat_id] != student_number:
                return False, "Only the student who logged into this seat can check out."
            del self._owners[seat_id]
            cleared = True

        if seat_id in self._reservations:
            res_list = self._reservations[seat_id]
            self._reservations[seat_id] = [
                res for res in res_list if res["student"] != student_number
            ]
            if len(self._reservations[seat_id]) == 0:
                del self._reservations[seat_id]
            cleared = True

        if cleared:
            return True, f"Seat {seat_id} is now fully available."
        
        return False, "This seat is already available."