import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/robot_model.dart';

class RobotProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  List<Robot> _robots = [];
  Robot? _selectedRobot;
  bool _isLoading = false;
  String? _error;

  List<Robot> get robots => _robots;
  Robot? get selectedRobot => _selectedRobot;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isConnected => _selectedRobot != null;

  Future<void> loadRobots() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _robots = await _apiService.getRobots();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> addRobot(String name, String serialNumber) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final newRobot = await _apiService.registerRobot(name, serialNumber);
      _robots.add(newRobot);
    } catch (e) {
      _error = e.toString();
      rethrow;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void selectRobot(Robot robot) {
    _selectedRobot = robot;
    notifyListeners();
  }

  void disconnect() {
    _selectedRobot = null;
    notifyListeners();
  }
}
