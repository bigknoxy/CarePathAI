namespace CarePath.Domain.DTOs;

public class PatientDto
{
    public int Id { get; set; }
    public required string FirstName { get; set; }
    public required string LastName { get; set; }
    public required string DateOfBirth { get; set; }
    public required string MedicalRecordNumber { get; set; }
}