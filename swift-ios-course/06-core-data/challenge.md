# Challenge 06 — Persistence in Depth

Solution in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Edit + persist.** Add a detail screen that edits a `PlaceItem`'s name/notes and
   persists the change (SwiftData autosaves; just mutate the model). Confirm edits survive
   relaunch.

2. **Seed once.** On first launch (empty store), insert the sample places; on later
   launches, don't duplicate them. (Hint: check `places.isEmpty` in `.task`/`onAppear`,
   or store a `@AppStorage("seeded")` flag.)

3. **A relationship.** Add a `Tag` `@Model` with a to-many relationship from
   `PlaceItem` (`var tags: [Tag]`). Add a tag to a place and show its tags. (In Core Data,
   describe how you'd model the same relationship with `NSRelationshipDescription`.)

4. **Predicate practice.** Add a search field that drives a `#Predicate<PlaceItem>` to
   filter by name (case-insensitive). Then write the equivalent `NSPredicate(format:)`
   string for Core Data and note the difference (type-safe vs string).

5. **Stretch:** Migrate the in-memory `PlaceStore` from earlier modules so the network
   `reload()` writes fetched places into SwiftData (insert if new by `id`), making the
   app offline-first via the store rather than a JSON cache.

## Success criteria
- [ ] Editing persists across relaunch.
- [ ] Seeding happens exactly once (no duplicates).
- [ ] A working to-many relationship; correct Core Data modeling description.
- [ ] A `#Predicate` search and its `NSPredicate` equivalent.
