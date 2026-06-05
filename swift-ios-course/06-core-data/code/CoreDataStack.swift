import CoreData

// A Core Data stack whose model is built IN CODE (no binary .xcdatamodeld), so it's
// reviewable and runnable. In a real app you'd typically design the model in Xcode's
// visual editor and just use `NSPersistentContainer(name: "Places")`.
enum CoreDataStack {
    static let shared = makeContainer()

    static func makeContainer(inMemory: Bool = false) -> NSPersistentContainer {
        let model = NSManagedObjectModel()

        let entity = NSEntityDescription()
        entity.name = "CDPlace"
        entity.managedObjectClassName = NSStringFromClass(CDPlace.self)
        entity.properties = [
            attribute("id", .UUIDAttributeType),
            attribute("name", .stringAttributeType),
            attribute("notes", .stringAttributeType, optional: true),
            attribute("latitude", .doubleAttributeType),
            attribute("longitude", .doubleAttributeType),
        ]
        model.entities = [entity]

        let container = NSPersistentContainer(name: "Places", managedObjectModel: model)
        if inMemory {
            container.persistentStoreDescriptions.first?.url = URL(fileURLWithPath: "/dev/null")
        }
        container.loadPersistentStores { _, error in
            if let error { fatalError("Core Data failed to load: \(error)") }
        }
        container.viewContext.automaticallyMergesChangesFromParent = true
        return container
    }

    private static func attribute(_ name: String, _ type: NSAttributeType,
                                  optional: Bool = false) -> NSAttributeDescription {
        let a = NSAttributeDescription()
        a.name = name
        a.attributeType = type
        a.isOptional = optional
        return a
    }
}

// The managed-object subclass. @objc(CDPlace) + managedObjectClassName above wire it up.
@objc(CDPlace)
final class CDPlace: NSManagedObject {
    @NSManaged var id: UUID
    @NSManaged var name: String
    @NSManaged var notes: String?
    @NSManaged var latitude: Double
    @NSManaged var longitude: Double
}

extension CDPlace {
    static func fetchAll() -> NSFetchRequest<CDPlace> {
        let request = NSFetchRequest<CDPlace>(entityName: "CDPlace")
        request.sortDescriptors = [NSSortDescriptor(key: "name", ascending: true)]
        return request
    }
}
