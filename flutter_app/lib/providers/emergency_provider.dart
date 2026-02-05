import 'package:flutter/material.dart';
import '../services/api_service.dart';

class EmergencyProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  List<dynamic> _contacts = [];
  bool _isLoading = false;
  String? _error;

  List<dynamic> get contacts => _contacts;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadContacts() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _contacts = await _apiService.getEmergencyContacts();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> addContact(String name, String phone, String relation) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      await _apiService.addEmergencyContact(name, phone, relation);
      await loadContacts(); // Reload list
    } catch (e) {
      _error = e.toString();
      rethrow;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> triggerEmergency() async {
    _isLoading = true;
    notifyListeners();
    try {
      await _apiService.triggerEmergency();
    } catch (e) {
      _error = e.toString();
      rethrow;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
