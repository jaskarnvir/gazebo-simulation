class Robot {
  final int id;
  final String serialNumber;
  final String name;
  final String modelType;
  final bool isOnline;
  final int ownerId;

  Robot({
    required this.id,
    required this.serialNumber,
    required this.name,
    required this.modelType,
    required this.isOnline,
    required this.ownerId,
  });

  factory Robot.fromJson(Map<String, dynamic> json) {
    return Robot(
      id: json['id'],
      serialNumber: json['serial_number'],
      name: json['name'],
      modelType: json['model_type'] ?? 'MiRo-e',
      isOnline: json['is_online'] ?? false,
      ownerId: json['owner_id'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'serial_number': serialNumber,
      'name': name,
      'model_type': modelType,
      'is_online': isOnline,
      'owner_id': ownerId,
    };
  }
}
