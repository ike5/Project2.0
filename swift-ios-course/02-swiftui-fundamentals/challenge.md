# Challenge 02 — Extend PlacesApp

Reference solution in [`solutions/`](./solutions/). Try first — small edits to PlacesApp.

## Tasks
1. **Edit a place.** Make `PlaceDetailView` editable: add an "Edit" toolbar button that
   presents a sheet (reuse/adapt `AddPlaceView`) pre-filled with the place, and save the
   changes back into the store. (Hint: give `PlaceStore` an `update(_ place: Place)` that
   replaces by `id`.)

2. **Favorites.** Add `var isFavorite = false` to `Place`, a star toggle in the row
   (`Button`/`Image(systemName:)`), and a filter control (`Picker` or `.searchable`-style
   segmented control) to show All vs Favorites.

3. **Search.** Add `.searchable(text:)` to the list and filter `store.places` by name.

4. **Sort.** Add a toolbar menu to sort by name or by most-recently-added.

5. **Stretch:** Persist nothing yet (that's Module 06) — but factor the row into its own
   `PlaceRow` view that takes a `Place` and a `@Binding<Bool>` for the favorite, to
   practice bindings between parent and child.

## Success criteria
- [ ] Editing a place updates the list (matched by `id`).
- [ ] Favorite toggling works and a filter shows only favorites.
- [ ] `.searchable` filters the list by name.
- [ ] Sorting reorders the list.
- [ ] (Stretch) A reusable `PlaceRow` child view with a `@Binding`.
