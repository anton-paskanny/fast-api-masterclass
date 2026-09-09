<!-- markdownlint-disable-file -->

# Query Options

OPTION A: Fetching the booking by itself

```python
await session.get(Booking, 1)
```

```sql
SELECT *
FROM bookings
WHERE bookings.id = 1;
```

```
id | user_id | room_id | check_in   | check_out
-----------------------------------------------
1  | 1       | 1       | 2026-06-01 | 2026-06-03
```

---------------------------------------------------------------

OPTION B: Fetching the booking, fetching the room (`selectin`)

```python
await session.get(Booking, 1, options=[selectinload(Booking.room)])
```

```sql
SELECT *
FROM bookings
WHERE bookings.id = 1;
```

```
id | user_id | room_id | check_in   | check_out
-----------------------------------------------
1  | 1       | 1       | 2026-06-01 | 2026-06-03
```

-> Returns a booking that has a `room_id` of 1.

```sql
SELECT *
FROM rooms
WHERE rooms.id IN (1);
```

```
id | name       | price_per_night | bedrooms | bathrooms
--------------------------------------------------------
1  | Cool Villa | 200             | 4.0      | 2.5
```

---------------------------------------------------------------

OPTION C: Fetching the booking, joining the room

A booking has one room, so we'll left join the complementary
room data.

```python
await session.get(Booking, 1, options=[joinedload(Booking.room)])
```

```sql
SELECT
  bookings.id,
  bookings.user_id,
  bookings.room_id,
  bookings.check_in,
  bookings.check_out,
  rooms.name,
  rooms.price_per_night,
  rooms.bedrooms,
  rooms.bathrooms
FROM bookings
LEFT JOIN rooms ON bookings.room_id = rooms.id
WHERE bookings.id = 1;
```

```
id | user_id | room_id | check_in   | check_out  | name       | price_per_night | bedrooms | bathrooms
-------------------------------------------------------------------------------------------------------
1  | 1       | 1       | 2026-06-01 | 2026-06-03 | Cool Villa | 200             | 4.0      | 2.5
```

---------------------------------------------------------------

OPTION D: Fetching the booking, joining the room, joining the room amenities

Imagine a room has amenities (A/C, laundry, WiFi) and each one is connected
to the room in an `amenities` table.

```
room_id | amenity
-----------------
1       | WiFi
1       | Pool
1       | Parking
1       | Desk
```

What happens if we start from a booking and pull its amenities? We create multiple rows.

```python
await session.get(Booking, 1, options=[joinedload(Booking.room).joinedload(Room.amenities)])
```

1 booking × 1 room x 4 amenities = 4 total rows!

```sql
SELECT
  bookings.id,
  bookings.user_id,
  bookings.room_id,
  bookings.check_in,
  bookings.check_out,
  rooms.name,
  rooms.price_per_night,
  rooms.bedrooms,
  rooms.bathrooms,
  amenities.amenity
FROM bookings
LEFT JOIN rooms ON bookings.room_id = rooms.id
LEFT JOIN amenities ON rooms.id = amenities.room_id
WHERE bookings.id = 1;
```

```
id | user_id | room_id | check_in   | check_out  | name       | price_per_night | bedrooms | bathrooms | amenity
----------------------------------------------------------------------------------------------------------------
1  | 1       | 1       | 2026-06-01 | 2026-06-03 | Cool Villa | 200             | 4.0      | 2.5       | WiFi
1  | 1       | 1       | 2026-06-01 | 2026-06-03 | Cool Villa | 200             | 4.0      | 2.5       | Pool
1  | 1       | 1       | 2026-06-01 | 2026-06-03 | Cool Villa | 200             | 4.0      | 2.5       | Parking
1  | 1       | 1       | 2026-06-01 | 2026-06-03 | Cool Villa | 200             | 4.0      | 2.5       | Desk
```

We have to be careful because a database request for a single booking can give the impression of 4 bookings!
The data balloons to accommodate the one-to-many association (one booking to many amenities through a room).
For these situations, joining everything in one query may not be the best idea!

It's better to join the booking with the room info (one row), then make a separate fetch for all amenities
belonging to the room.